import flet as ft
from utils.utils import (
    CARD_BG_COLOR,
    PRIMARY_BLUE,
    TEXT_PRIMARY,
    TEXT_SECONDARY,
    BORDER_COLOR,
)


class EvaluationProgressDialog:
    """
    Modal progress dialog displayed during AI model evaluation.
    Provides live status, file detail, and a progress bar.
    """
    def __init__(self, title: str = "Evaluating Responses", subtitle: str = "BERT Semantic Evaluation in progress..."):
        self.page = None
        self.title_text = ft.Text(title, size=17, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)
        self.subtitle_text = ft.Text(subtitle, size=12, color=TEXT_SECONDARY)
        
        self.spinner = ft.ProgressRing(width=28, height=28, stroke_width=3, color=PRIMARY_BLUE)
        self.status_label = ft.Text(
            "Initializing evaluation model...",
            size=13,
            weight=ft.FontWeight.W_600,
            color=TEXT_PRIMARY,
            no_wrap=False,
        )
        self.detail_label = ft.Text(
            "Loading neural network weights...",
            size=12,
            color=TEXT_SECONDARY,
            no_wrap=False,
        )
        self.progress_bar = ft.ProgressBar(
            value=None,
            color=PRIMARY_BLUE,
            bgcolor="#e2e8f0",
            height=6,
            border_radius=3,
        )
        self.percent_label = ft.Text("", size=11, weight=ft.FontWeight.BOLD, color=PRIMARY_BLUE)

        content = ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Icon(ft.Icons.AUTO_AWESOME, color=PRIMARY_BLUE, size=20),
                                width=36,
                                height=36,
                                border_radius=18,
                                bgcolor="#eff6ff",
                                alignment=ft.alignment.center,
                            ),
                            ft.Column(
                                [
                                    self.title_text,
                                    self.subtitle_text,
                                ],
                                spacing=2,
                                expand=True,
                            ),
                        ],
                        spacing=12,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Divider(height=16, color=BORDER_COLOR),
                    ft.Row(
                        [
                            self.spinner,
                            ft.Column(
                                [
                                    self.status_label,
                                    self.detail_label,
                                ],
                                spacing=2,
                                expand=True,
                            ),
                        ],
                        spacing=14,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(height=8),
                    self.progress_bar,
                    ft.Row(
                        [
                            ft.Text("Please wait, do not close the window.", size=11, color=TEXT_SECONDARY, italic=True),
                            self.percent_label,
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                ],
                tight=True,
                spacing=6,
            ),
            width=440,
            padding=ft.padding.symmetric(horizontal=8, vertical=4),
        )

        self.dialog = ft.AlertDialog(
            modal=True,
            content=content,
            bgcolor=CARD_BG_COLOR,
            shape=ft.RoundedRectangleBorder(radius=12),
        )

    def open(self, page: ft.Page):
        self.page = page
        try:
            page.open(self.dialog)
        except Exception:
            page.dialog = self.dialog
            self.dialog.open = True
            try:
                page.update()
            except Exception:
                pass

    def update_progress(self, status: str = None, detail: str = None, progress_pct: float = None):
        if status is not None:
            self.status_label.value = status
        if detail is not None:
            self.detail_label.value = detail
        if progress_pct is not None:
            clamped = max(0.0, min(1.0, float(progress_pct)))
            self.progress_bar.value = clamped
            self.percent_label.value = f"{int(clamped * 100)}%"
        else:
            self.progress_bar.value = None
            self.percent_label.value = ""

        if self.page:
            try:
                self.dialog.update()
            except Exception:
                try:
                    self.page.update()
                except Exception:
                    pass

    def close(self):
        if self.page:
            try:
                self.page.close(self.dialog)
            except Exception:
                self.dialog.open = False
                try:
                    self.page.update()
                except Exception:
                    pass
