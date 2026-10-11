# QualCheck

QualCheck is a rubric-guided semantic evaluation system for academic responses. It is a Python desktop application built with Flet that evaluates short answers, essays, and code reports using fine-tuned BERT encoders, cosine similarity, and calibrated relevance thresholds.

The system is intended for evaluators and administrators:

- Evaluators create an academic prompt, define rubric criteria, upload student PDF responses, and review scores.
- Administrators manage users, inspect submissions, view analytics, and review audit activity.
- Evaluation history, rubrics, profiles, and activity records are stored in Supabase.

## Features

### Evaluation

- Supports three output types:
  - Short Answer
  - Essay
  - Code Report
- Accepts one or more PDF responses per evaluation.
- Extracts and normalizes text from uploaded PDFs.
- Uses a separate fine-tuned model and threshold metadata for each output type.
- Produces a cosine similarity score and one of three classifications:
  - Fully Relevant
  - Partially Relevant
  - Irrelevant
- Displays criterion scores and stores evaluation results for later review.

### Authentication and account management

- Email and password authentication through Supabase Auth.
- Google authentication support where configured.
- Persistent local sessions with token refresh.
- Account creation and password reset flows.
- Password strength validation.
- Active-account checks during session restoration.
- Role-based access for evaluator and administrator accounts.

### Dashboard and administration

- Evaluation history and summary statistics.
- Classification distribution and average-score views.
- User management for administrators.
- Submission review.
- Audit and user-activity records.
- Profile and avatar management.

## How the evaluation pipeline works

1. The user selects an output type.
2. The user enters an academic prompt and rubric criteria.
3. One or more student PDF files are selected.
4. `PDFProcessor` extracts and normalizes the response text.
5. `EmbeddingGenerator` loads the selected BERT checkpoint and creates embeddings.
6. `Evaluator` calculates cosine similarity between the prompt/rubric embedding and the response embedding.
7. The similarity score is classified using `theta1` and `theta2` from the selected model metadata file.
8. The result is displayed and saved to the Supabase `evaluations` table.

The three evaluation tracks use separate model artifacts:

| Output type | Weights directory | Weight file | Metadata file |
|---|---|---|---|
| Short Answer | `qualcheck_short_answers/` | `qualcheck_short_answers_final.safetensors` | `qualcheck_short_answers_final_meta.json` |
| Essay | `essay_qualcheck/` | `qualcheck_final.safetensors` | `qualcheck_final_meta.json` |
| Code Report | `codereport_bert/` | `best_model.safetensors` | `qualcheck_final_meta.json` |

Model artifacts are local files and are ignored by Git. They must be supplied separately before running the corresponding evaluation track.

## Technology stack

- Python
- Flet 0.28.3
- Supabase Python client
- Supabase Auth and PostgreSQL
- Supabase Storage
- Hugging Face Transformers
- PyTorch
- Safetensors
- NumPy
- pypdf
- python-dotenv
- Cloudinary for optional media handling

See [`requirements.txt`](./requirements.txt) for the complete dependency list.

## Project structure

```text
THESIS_2_BOSS_BATTLE/
├── core/
│   ├── embeddings.py        BERT loading and embedding generation
│   ├── evaluation.py        Similarity scoring and classification
│   └── pdf_processor.py     PDF extraction and text preprocessing
├── database/
│   ├── auth.py              Authentication helpers
│   ├── models.py            Data models
│   └── supabase_schema.sql  Database schema and row-level security
├── navigation/
│   ├── navigation.py        Evaluator navigation
│   └── admin_navigation.py  Administrator navigation
├── screens/
│   ├── ui_short_answer.py   Short-answer evaluation
│   ├── ui_essay.py          Essay evaluation
│   ├── ui_code_report.py    Code-report evaluation
│   ├── ui_dashboard.py      Evaluation dashboard
│   ├── ui_login.py          Login and authentication
│   └── ui_admin*.py         Administrator screens
├── services/
│   ├── supabase_client.py   Supabase client creation
│   ├── session_manager.py   Local session persistence
│   ├── email_service.py     SMTP email operations
│   ├── analytics_service.py Dashboard queries
│   └── ...                  Account, audit, media, and submission services
├── widgets/
│   ├── loading_components.py Shared loading and progress controls
│   └── snackbar.py          Success and error notifications
├── utils/
│   └── utils.py             Shared UI constants and styling
├── main.py                  Application entry point
├── requirements.txt         Python dependencies
└── .env.example             Environment variable template
```

## Requirements

- Python 3.10 or newer is recommended.
- A Supabase project.
- A local copy of the required model weights and metadata.
- Internet access when dependencies or the base BERT model are not already cached.
- A configured SMTP provider if account and password-reset emails are required.

The application loads `bert-base-uncased` from the local Hugging Face cache when available. If it is not cached, Transformers attempts to download it.

## Installation

Clone the repository and enter the project directory:

```bash
git clone <repository-url>
cd THESIS_2_BOSS_BATTLE
```

Create and activate a virtual environment:

```bash
python -m venv .venv
```

On Windows:

```powershell
.venv\Scripts\Activate.ps1
```

On macOS or Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Configuration

Copy the environment template:

```powershell
Copy-Item .env.example .env
```

Set the Supabase values in `.env`:

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key
```

The service-role key is privileged and must not be exposed in source control or distributed to end users. Use the anon key for normal client operations and rely on Supabase row-level security policies.

### Optional SMTP configuration

Email delivery is implemented but depends on valid SMTP configuration. Add these variables only when email notifications, welcome emails, or password reset emails are needed:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=your-sender@example.com
SMTP_PASSWORD=your-smtp-password-or-app-password
SMTP_FROM_NAME=QualCheck
SMTP_USE_TLS=true
```

For Gmail, use an app password where required. Do not commit SMTP credentials. If these values are missing or invalid, the application cannot reliably send email even though the email service code is present.

### Optional Cloudinary configuration

If the avatar or media integration is enabled, configure the Cloudinary credentials required by the active service implementation. Do not place production credentials in the repository.

## Database setup

1. Create a Supabase project.
2. Open the Supabase SQL Editor.
3. Run [`database/supabase_schema.sql`](./database/supabase_schema.sql).
4. Configure the required authentication providers in Supabase.
5. Create and configure any required storage buckets and policies.
6. Add the resulting project URL and keys to `.env`.

The schema creates and configures:

- `profiles`
- `rubrics`
- `evaluations`
- `audit_logs`
- `user_activities`
- `password_resets`

It also creates indexes, the administrator helper function, and row-level security policies. Review the policies before production deployment and verify that they match the intended organization and tenant boundaries.

Additional Supabase notes are available in [`supabase_wiring_instructions.txt`](./supabase_wiring_instructions.txt).

## Model artifact setup

Place the model files in these directories at the project root:

```text
qualcheck_short_answers/
    qualcheck_short_answers_final.safetensors
    qualcheck_short_answers_final_meta.json

essay_qualcheck/
    qualcheck_final.safetensors
    qualcheck_final_meta.json

codereport_bert/
    best_model.safetensors
    qualcheck_final_meta.json
```

The screen modules define the paths explicitly:

- [`screens/ui_short_answer.py`](./screens/ui_short_answer.py)
- [`screens/ui_essay.py`](./screens/ui_essay.py)
- [`screens/ui_code_report.py`](./screens/ui_code_report.py)

The metadata files contain the thresholds used by [`core/evaluation.py`](./core/evaluation.py). The constructor requires a metadata path so that one evaluation track cannot silently fall back to another track's thresholds.

## Running the application

Start the Flet application from the project root:

```bash
python main.py
```

The application opens the login screen. After authentication, evaluators can create a new evaluation or review their dashboard. Users with the administrator role can open the administrator panel.

## Testing and validation

Run the available test suite with:

```bash
pytest
```

For a basic import or startup check:

```bash
python -c "import main; print('QualCheck imports successfully')"
```

Before testing an evaluation workflow, verify that:

1. The `.env` file contains valid Supabase credentials.
2. The required model files exist.
3. The BERT base model is available locally or the machine can access Hugging Face.
4. The test user has the correct Supabase role.
5. PDF files contain selectable text. Scanned image-only PDFs may produce little or no extracted text without OCR.

## Security considerations

- Never commit `.env`, service-role keys, SMTP passwords, model credentials, or session files.
- Keep Supabase row-level security enabled.
- Do not use the service-role key in distributed client-side workflows.
- Treat uploaded PDF content as untrusted input.
- Review the current SMTP behavior before using the application in production.
- Remove or rotate test credentials before deployment.
- Restrict administrator accounts and verify role checks on every administrator route.

## Known limitations

- Email sending is configuration-dependent and is not guaranteed to work without a valid SMTP provider and credentials.
- PDF extraction depends on selectable text; image-only documents require OCR support that is not currently part of the core processor.
- Model artifact directories are not included in the repository and must be provisioned separately.
- The application uses local session storage through `.session.json`; protect the machine and user profile where the application runs.
- Evaluation quality depends on the fine-tuned checkpoint, threshold metadata, input quality, and rubric quality.
- Some dependencies in `requirements.txt` support planned or backend integrations and may not be imported by every desktop workflow.

## Documentation

- [`REVIEWER.md`](./REVIEWER.md) contains a codebase review and presentation guide.
- [`qualcheck_design_spec.md`](./qualcheck_design_spec.md) describes the intended UI design and screen behavior.
- [`supabase_wiring_instructions.txt`](./supabase_wiring_instructions.txt) describes Supabase integration steps.
- [`database/supabase_schema.sql`](./database/supabase_schema.sql) defines the database schema and security policies.
- [Architecture diagram](./.github/modernize/assessment/engines/facts/architecture-diagram.md) documents the application layers and component relationships.

## License

Add the project's license terms here before public distribution.
