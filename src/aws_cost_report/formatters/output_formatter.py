#!/usr/bin/env python3

import logging
from datetime import datetime

from tabulate import tabulate

logger = logging.getLogger(__name__)


class OutputFormatter:
    """レポート出力のフォーマットを担当するクラス"""

    def __init__(self, format_type="console", output_file=None):
        """
        出力フォーマッタを初期化

        Args:
            format_type (str): 出力形式 ('console', 'csv', 'html')
            output_file (str): 出力ファイル名 (format_typeがconsole以外の場合に使用)
        """
        self.format_type = format_type
        self.output_file = output_file

    def format_service_summary(self, service_summary_df, currency="USD"):
        """
        サービス概要のフォーマット

        Args:
            service_summary_df (DataFrame): サービス概要のDataFrame
            currency (str): 通貨単位

        Returns:
            str または None: フォーマット結果、consoleモードの場合はNone
        """
        if self.format_type == "console":
            service_display = service_summary_df.rename(
                columns={"Cost": f"Cost ({currency})"}
            )
            print("\n=== SERVICE SUMMARY ===")
            print(
                tabulate(
                    service_display, headers="keys", tablefmt="psql", floatfmt=".2f"
                )
            )
            return None

        elif self.format_type == "html":
            return service_summary_df.rename(
                columns={"Cost": f"Cost ({currency})"}
            ).to_html(index=False, classes="dataframe", float_format="%.2f")

        elif self.format_type == "csv":
            if self.output_file:
                service_file = f"service_{self.output_file}"
                service_summary_df.to_csv(service_file, index=False)
                logger.info(f"Service summary saved to {service_file}")
            return None

    def format_resource_summary(self, resource_summary_df, currency="USD"):
        """
        リソース概要のフォーマット

        Args:
            resource_summary_df (DataFrame): リソース概要のDataFrame
            currency (str): 通貨単位

        Returns:
            str または None: フォーマット結果、consoleモードの場合はNone
        """
        if self.format_type == "console":
            resource_display = resource_summary_df.rename(
                columns={"Cost": f"Cost ({currency})"}
            )
            print("\n=== RESOURCE DETAILS ===")
            print(
                tabulate(
                    resource_display, headers="keys", tablefmt="psql", floatfmt=".2f"
                )
            )
            return None

        elif self.format_type == "html":
            return resource_summary_df.rename(
                columns={"Cost": f"Cost ({currency})"}
            ).to_html(index=False, classes="dataframe", float_format="%.2f")

        elif self.format_type == "csv":
            if self.output_file:
                resource_summary_df.to_csv(self.output_file, index=False)
                logger.info(f"Resource summary saved to {self.output_file}")
            return None

    def generate_html_report(
        self, service_summary_html, resource_summary_html, start_date, end_date
    ):
        """
        HTML形式のレポートを生成

        Args:
            service_summary_html (str): サービス概要のHTML
            resource_summary_html (str): リソース概要のHTML
            start_date (str): 期間開始日
            end_date (str): 期間終了日

        Returns:
            str: 完成したHTMLレポート
        """
        html_output = f"""
        <html>
        <head>
            <title>AWS Cost Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; position: sticky; top: 0; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                tr:hover {{ background-color: #f1f1f1; }}
                .summary {{ margin-bottom: 30px; }}
                h1, h2 {{ color: #333; }}
                .cost {{ text-align: right; }}
            </style>
        </head>
        <body>
            <h1>AWS Cost Report ({start_date} to {end_date})</h1>

            <div class="summary">
                <h2>Service Summary</h2>
                {service_summary_html}
            </div>

            <div class="details">
                <h2>Resource Details</h2>
                {resource_summary_html}
            </div>
            <p>
                <small>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small>
            </p>
        </body>
        </html>
        """
        return html_output

    def save_report(self, html_content):
        """
        レポートを保存

        Args:
            html_content (str): 保存するHTMLコンテンツ
        """
        if self.format_type == "html" and self.output_file:
            with open(self.output_file.replace(".csv", ".html"), "w") as f:
                f.write(html_content)
            logger.info(
                f"HTML report saved to {self.output_file.replace('.csv', '.html')}"
            )
