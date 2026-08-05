"""
Embedding generation module for QualCheck
Loads the fine-tuned Siamese BERT encoder from safetensors and generates
mean-pooled sentence embeddings for cosine-similarity scoring.
"""

import torch
from transformers import AutoTokenizer, AutoModel
from safetensors.torch import load_file


class EmbeddingGenerator:
    """Generate embeddings using the fine-tuned BERT encoder."""

    def __init__(
        self,
        model_dir: str,
        bert_model: str = "bert-base-uncased",
        max_len: int = 128,
        device: str = None,
    ):
        """
        Args:
            model_dir: Path to the .safetensors checkpoint
                       (e.g. qualcheck_short_answers/qualcheck_short_answers_final.safetensors)
            bert_model: Base architecture the checkpoint was fine-tuned from
            max_len: Max token length (must match training — 128 for short answer)
            device: "cuda" / "cpu". Auto-detected if not given.
        """
        self.max_len = max_len
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")

        self.tokenizer, self.model = self._load_base(bert_model)

        self._load_weights(model_dir)

        self.model.to(self.device)
        self.model.eval()

    @staticmethod
    def _load_base(bert_model: str):
        """Load tokenizer/model from local HF cache if present; only hit the
        network if bert-base-uncased hasn't been downloaded yet."""
        try:
            tokenizer = AutoTokenizer.from_pretrained(bert_model, local_files_only=True)
            model = AutoModel.from_pretrained(bert_model, local_files_only=True)
        except OSError:
            tokenizer = AutoTokenizer.from_pretrained(bert_model)
            model = AutoModel.from_pretrained(bert_model)
        return tokenizer, model

    def _load_weights(self, model_dir: str):
        """Load fine-tuned weights from a raw safetensors state_dict."""
        state_dict = load_file(model_dir)

        # Some training loops save with a wrapper prefix (e.g. "bert.", "encoder.").
        # Strip the most common ones so keys line up with a stock AutoModel.
        cleaned = {}
        for k, v in state_dict.items():
            new_k = k
            for prefix in ("bert.", "encoder.", "model."):
                if new_k.startswith(prefix):
                    new_k = new_k[len(prefix):]
                    break
            cleaned[new_k] = v

        missing, unexpected = self.model.load_state_dict(cleaned, strict=False)
        unexpected_classifier = [k for k in unexpected if k.startswith("classifier.")]
        unexpected_other = [k for k in unexpected if not k.startswith("classifier.")]

        if missing or unexpected_other:
            print(
                f"[EmbeddingGenerator] WARNING: {len(missing)} missing / "
                f"{len(unexpected_other)} unexpected keys loading '{model_dir}'. "
                f"If this list is long, the checkpoint's module structure doesn't "
                f"match a stock AutoModel — send the Phase 4 model class to fix key mapping."
            )
            if missing:
                print(f"  missing (first 5): {missing[:5]}")
            if unexpected_other:
                print(f"  unexpected (first 5): {unexpected_other[:5]}")
        elif unexpected_classifier:
            print(
                f"[EmbeddingGenerator] Loaded encoder weights from '{model_dir}' and ignored "
                f"{len(unexpected_classifier)} classifier-head keys from the training checkpoint "
                f"(expected — embeddings only use the encoder, not the classifier)."
            )

    @staticmethod
    def _cls_pool(last_hidden_state: torch.Tensor) -> torch.Tensor:
        """CLS-token pooling — matches QualCheckModel.encode(), which uses
        last_hidden_state[:, 0, :], NOT mean pooling. The model was only ever
        supervised to make the CLS token discriminative."""
        return last_hidden_state[:, 0, :]

    @torch.no_grad()
    def encode_pair(self, text_a: str, text_b: str) -> list:
        """
        Encode a BERT sentence pair as ONE joint sequence:
        [CLS] text_a [SEP] text_b [SEP]
        This matches QualCheckDataset._enc(a, b) and is how the P-side
        (question, full_rubric) is embedded during training — NOT two
        independent single-sentence embeddings compared afterward.
        """
        encoded = self.tokenizer(
            text_a, text_b,
            add_special_tokens=True,
            max_length=self.max_len,
            padding="max_length",
            truncation=True,
            return_attention_mask=True,
            return_tensors="pt",
        ).to(self.device)
        outputs = self.model(**encoded)
        cls = self._cls_pool(outputs.last_hidden_state)
        return cls.cpu().tolist()[0]

    @torch.no_grad()
    def encode_single(self, text: str) -> list:
        """
        Encode a single sequence: [CLS] text [SEP]
        This matches QualCheckDataset._enc(a) with b=None, used for the
        R-side (student response).
        """
        encoded = self.tokenizer(
            text,
            add_special_tokens=True,
            max_length=self.max_len,
            padding="max_length",
            truncation=True,
            return_attention_mask=True,
            return_tensors="pt",
        ).to(self.device)
        outputs = self.model(**encoded)
        cls = self._cls_pool(outputs.last_hidden_state)
        return cls.cpu().tolist()[0]

    # --- Legacy single-text batch API -------------------------------------
    # Kept only for scripts/tools that want a generic embedding. NOT used by
    # Evaluator.evaluate_response() anymore — that calls encode_pair/encode_single
    # directly since the model's P-side and R-side inputs aren't symmetric.
    @torch.no_grad()
    def generate_embedding(self, text: str) -> list:
        return self.encode_single(text)

    @torch.no_grad()
    def generate_embeddings_batch(self, texts: list) -> list:
        return [self.encode_single(t) for t in texts]