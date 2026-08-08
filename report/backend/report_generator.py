from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
import os


def generate_report(data, output_path):

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    document = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleCustom",
        parent=styles["Title"],
        fontSize=24,
        leading=30,
        alignment=1,
        spaceAfter=20
    )

    heading_style = ParagraphStyle(
        "HeadingCustom",
        parent=styles["Heading2"],
        fontSize=16,
        leading=20,
        spaceBefore=15,
        spaceAfter=10
    )

    normal_style = ParagraphStyle(
        "NormalCustom",
        parent=styles["BodyText"],
        fontSize=10,
        leading=15,
        spaceAfter=8
    )

    story = []

    # --------------------------------
    # TITLE
    # --------------------------------

    story.append(
        Paragraph("VENTURE X-RAY", title_style)
    )

    story.append(
        Paragraph(
            "Final Startup Analysis Report",
            styles["Heading1"]
        )
    )

    story.append(Spacer(1, 20))

    startup = data.startup
    refined = data.refined_idea

    startup_name = startup.get(
        "name",
        "Startup"
    )

    story.append(
        Paragraph(
            f"<b>Startup:</b> {startup_name}",
            normal_style
        )
    )

    story.append(
        Paragraph(
            f"<b>Defense Score:</b> "
            f"{data.defense_score}/100",
            normal_style
        )
    )

    story.append(
        Paragraph(
            f"<b>Final Decision:</b> "
            f"{data.decision}",
            normal_style
        )
    )

    # --------------------------------
    # STARTUP OVERVIEW
    # --------------------------------

    story.append(
        Paragraph(
            "1. Startup Overview",
            heading_style
        )
    )

    for key, value in startup.items():

        story.append(
            Paragraph(
                f"<b>{key.replace('_', ' ').title()}:</b> "
                f"{value}",
                normal_style
            )
        )

    # --------------------------------
    # REFINED IDEA
    # --------------------------------

    story.append(
        Paragraph(
            "2. Refined Startup Idea",
            heading_style
        )
    )

    for key, value in refined.items():

        story.append(
            Paragraph(
                f"<b>{key.replace('_', ' ').title()}:</b> "
                f"{value}",
                normal_style
            )
        )

    # --------------------------------
    # ATTACKER RESULTS
    # --------------------------------

    story.append(
        Paragraph(
            "3. AI Attacker Findings",
            heading_style
        )
    )

    if data.attacker_results:

        for index, attacker in enumerate(
            data.attacker_results,
            start=1
        ):

            story.append(
                Paragraph(
                    f"<b>Attacker {index}</b>",
                    normal_style
                )
            )

            for key, value in attacker.items():

                story.append(
                    Paragraph(
                        f"<b>{key.replace('_', ' ').title()}:</b> "
                        f"{value}",
                        normal_style
                    )
                )

    else:

        story.append(
            Paragraph(
                "No attacker findings available.",
                normal_style
            )
        )

    # --------------------------------
    # VULNERABILITIES
    # --------------------------------

    story.append(
        Paragraph(
            "4. Key Vulnerabilities",
            heading_style
        )
    )

    if data.vulnerabilities:

        vulnerability_data = [
            ["#", "Vulnerability"]
        ]

        for index, vulnerability in enumerate(
            data.vulnerabilities,
            start=1
        ):

            if isinstance(vulnerability, dict):

                text = ", ".join(
                    f"{key}: {value}"
                    for key, value in vulnerability.items()
                )

            else:

                text = str(vulnerability)

            vulnerability_data.append(
                [str(index), text]
            )

        table = Table(
            vulnerability_data,
            colWidths=[40, 450]
        )

        table.setStyle(
            TableStyle([
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    1,
                    colors.black
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.black
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.white
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                ),
                (
                    "PADDING",
                    (0, 0),
                    (-1, -1),
                    6
                )
            ])
        )

        story.append(table)

    else:

        story.append(
            Paragraph(
                "No vulnerabilities available.",
                normal_style
            )
        )

    # --------------------------------
    # DEFENSE SCORE
    # --------------------------------

    story.append(
        Paragraph(
            "5. Defense Analysis",
            heading_style
        )
    )

    story.append(
        Paragraph(
            f"The startup achieved a defense score of "
            f"<b>{data.defense_score}/100</b>.",
            normal_style
        )
    )

    if data.defense_score >= 80:

        assessment = "Strong defense capability."

    elif data.defense_score >= 60:

        assessment = (
            "Moderate defense capability. "
            "Further improvement is recommended."
        )

    else:

        assessment = (
            "Weak defense capability. "
            "Significant improvement is recommended."
        )

    story.append(
        Paragraph(
            f"<b>Assessment:</b> {assessment}",
            normal_style
        )
    )

    # --------------------------------
    # INVESTOR SIMULATION
    # --------------------------------

    story.append(
        Paragraph(
            "6. Investor Simulation",
            heading_style
        )
    )

    if data.investor_conversation:

        for index, conversation in enumerate(
            data.investor_conversation,
            start=1
        ):

            story.append(
                Paragraph(
                    f"<b>Conversation {index}</b>",
                    normal_style
                )
            )

            for key, value in conversation.items():

                story.append(
                    Paragraph(
                        f"<b>{key.replace('_', ' ').title()}:</b> "
                        f"{value}",
                        normal_style
                    )
                )

    else:

        story.append(
            Paragraph(
                "No investor conversation available.",
                normal_style
            )
        )

    # --------------------------------
    # FINAL RECOMMENDATION
    # --------------------------------

    story.append(
        Paragraph(
            "7. Final Recommendation",
            heading_style
        )
    )

    story.append(
        Paragraph(
            f"The final investment-readiness decision is "
            f"<b>{data.decision}</b>.",
            normal_style
        )
    )

    if data.decision.upper() == "STRONG":

        recommendation = (
            "The startup demonstrates strong potential "
            "and has successfully addressed major "
            "challenges identified during stress testing."
        )

    else:

        recommendation = (
            "The startup requires further refinement "
            "before it can be considered investment ready."
        )

    story.append(
        Paragraph(
            recommendation,
            normal_style
        )
    )

    story.append(Spacer(1, 30))

    story.append(
        Paragraph(
            "Generated by VentureX-Ray",
            normal_style
        )
    )

    document.build(story)

    return output_path