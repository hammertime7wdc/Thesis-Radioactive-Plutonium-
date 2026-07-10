import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import flet as ft
from services.audit_service import get_audit_logs, format_audit_log_detail
from utils.utils import (
    BG_COLOR, CARD_BG_COLOR, SECTION_BG_COLOR,
    PRIMARY_BLUE, PRIMARY_BLUE_DARK, PRIMARY_BLUE_LIGHT,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_TERTIARY, TEXT_WHITE,
    BORDER_COLOR, BORDER_COLOR_DARK,
    BUTTON_PRIMARY_BG, BUTTON_PRIMARY_TEXT, BUTTON_SECONDARY_BG, BUTTON_SECONDARY_TEXT, BUTTON_SECONDARY_BORDER,
    INPUT_BG, INPUT_BORDER, INPUT_TEXT, INPUT_HINT,
    SUCCESS, WARNING, ERROR
)


def main(page: ft.Page, nav=None):
    page.title = "QualCheck Admin - Settings & Audit"
    page.scroll = ft.ScrollMode.AUTO
    page.bgcolor = BG_COLOR

    # --- Admin Panel Header (fallback when not using admin navigation) ---
    if not nav:
        shield_icon = ft.Container(
            content=ft.Icon(ft.Icons.SHIELD, size=20, color=TEXT_WHITE),
            width=36,
            height=36,
            bgcolor="#a855f7",
            border_radius=8,
            alignment=ft.alignment.center,
        )

        admin_header = ft.Container(
            content=ft.Row(
                [
                    ft.Row(
                        [
                            shield_icon,
                            ft.Container(width=12),
                            ft.Column(
                                [
                                    ft.Text("Admin Panel", size=22, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                                    ft.Container(height=4),
                                    ft.Text("System administration & analytics", size=13, color=TEXT_SECONDARY),
                                ],
                                spacing=0,
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                        ],
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    ),
                    ft.Container(expand=True),
                    ft.Container(
                        content=ft.Text("Administrator", size=12, weight=ft.FontWeight.W_600, color="#7e22ce"),
                        padding=ft.padding.symmetric(horizontal=12, vertical=6),
                        bgcolor="#f3e8ff",
                        border_radius=16,
                    ),
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            padding=ft.padding.symmetric(horizontal=32, vertical=20),
        )
    else:
        admin_header = None

    # --- Audit Log Section (timeline-style matching the screenshot) ---
    def create_audit_entry(action_text, detail_text, user_email, timestamp):
        return ft.Container(
            content=ft.Row(
                [
                    ft.Icon(ft.Icons.ACCESS_TIME, size=16, color=TEXT_TERTIARY),
                    ft.Container(width=12),
                    ft.Column(
                        [
                            ft.Row(
                                [
                                    ft.Text(action_text, size=13, weight=ft.FontWeight.W_600, color=TEXT_PRIMARY),
                                    ft.Text("  —  ", size=13, color=TEXT_TERTIARY),
                                    ft.Text(detail_text, size=13, color=TEXT_SECONDARY),
                                ],
                                spacing=0,
                                wrap=True,
                            ),
                            ft.Container(height=2),
                            ft.Text(f"{user_email} · {timestamp}", size=12, color=TEXT_TERTIARY),
                        ],
                        spacing=0,
                        expand=True,
                    ),
                ],
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
            padding=ft.padding.symmetric(vertical=14),
            border=ft.border.only(bottom=ft.BorderSide(1, BORDER_COLOR)),
        )

    # Fetch real audit logs from database
    audit_logs_data = get_audit_logs(limit=50)

    # Format timestamp for display
    def format_timestamp(timestamp_str):
        """Format ISO timestamp to readable format"""
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M")
        except:
            return timestamp_str

    # Create audit entries from real data
    audit_entries_list = []
    for log in audit_logs_data:
        detail_text = format_audit_log_detail(log.get('detail'))
        timestamp = format_timestamp(log.get('created_at', ''))
        audit_entries_list.append(
            create_audit_entry(
                log.get('action', 'Unknown action'),
                detail_text,
                log.get('actor_email', 'Unknown user'),
                timestamp,
            )
        )

    # Show empty state if no logs
    if not audit_entries_list:
        audit_entries_list = [
            ft.Container(
                content=ft.Row(
                    [
                        ft.Icon(ft.Icons.HISTORY_OUTLINED, size=16, color=TEXT_TERTIARY),
                        ft.Container(width=12),
                        ft.Text("No audit logs found", size=13, color=TEXT_SECONDARY),
                    ],
                    spacing=0,
                ),
                padding=ft.padding.symmetric(vertical=12),
            )
        ]

    audit_entries = ft.Column(audit_entries_list, spacing=0)

    audit_section = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [
                        ft.Icon(ft.Icons.ACCESS_TIME, size=20, color=TEXT_TERTIARY),
                        ft.Container(width=8),
                        ft.Text("Audit Log", size=18, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                ft.Container(height=16),
                audit_entries,
            ],
            spacing=0,
        ),
        padding=ft.padding.all(24),
        bgcolor=CARD_BG_COLOR,
        border_radius=12,
        border=ft.border.all(1, BORDER_COLOR),
    )

    # --- Main Content ---
    if admin_header:
        main_content = ft.Container(
            content=ft.Column(
                [
                    admin_header,
                    ft.Container(height=8),
                    ft.Container(content=audit_section, padding=ft.padding.symmetric(horizontal=32)),
                    ft.Container(height=40),
                ],
                spacing=0,
            ),
        )
    else:
        main_content = ft.Container(
            content=ft.Column(
                [
                    ft.Container(content=audit_section, padding=ft.padding.symmetric(horizontal=32)),
                    ft.Container(height=40),
                ],
                spacing=0,
            ),
        )

    # --- Page Layout ---
    page.add(main_content)
    if nav:
        nav.main_content = main_content


if __name__ == "__main__":
    ft.app(target=main)