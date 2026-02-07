from fastapi.responses import StreamingResponse
import io
import frontmatter
from typing import List, Optional, Dict
from pathlib import Path

TEMPLATE_DIR = Path("backend/templates")

class TemplateService:
    @staticmethod
    def list_templates() -> List[Dict]:
        """Scans the template directory and returns metadata for all valid templates."""
        templates = []
        if not TEMPLATE_DIR.exists():
            return templates

        for file_path in TEMPLATE_DIR.glob("*.md"):
            try:
                post = frontmatter.load(file_path)
                templates.append({
                    "id": file_path.stem,
                    "title": post.metadata.get("title", file_path.stem),
                    "description": post.metadata.get("description", ""),
                    "type": post.metadata.get("type", "document"),
                    "format": post.metadata.get("format", "markdown"),
                    "version": post.metadata.get("version", "1.0"),
                    "author": post.metadata.get("author", "Unknown"),
                })
            except Exception as e:
                print(f"Error loading template {file_path}: {e}")
        
        return templates

    @staticmethod
    def get_template(template_id: str) -> Optional[Dict]:
        """Returns the full content and metadata for a specific template."""
        file_path = TEMPLATE_DIR / f"{template_id}.md"
        if not file_path.exists():
            return None
        
        post = frontmatter.load(file_path)
        return {
            "id": template_id,
            "content": post.content,
            **post.metadata
        }

class PolicyGeneratorService:
    def generate_policy(self, policy_type: str, company_name: str, industry: str) -> str:
        """
        Generates a markdown policy based on type and input parameters.
        """
        if policy_type == "aup":
            return self._generate_aup(company_name)
        elif policy_type == "itp":
            return self._generate_itp(company_name, industry)
        else:
            raise ValueError("Unknown policy type")

    def _generate_aup(self, company_name: str) -> str:
        return f"""# Acceptable Use Policy
**Organization:** {company_name}
**Date:** [Current Date]

## 1. Purpose
The purpose of this policy is to outline the acceptable use of computer equipment at {company_name}. These rules are in place to protect the employee and {company_name}. Inappropriate use exposes {company_name} to risks including virus attacks, compromise of network systems and services, and legal issues.

## 2. Scope
This policy applies to the use of information, electronic and computing devices, and network resources to conduct {company_name} business or interact with internal networks and business systems, whether owned or leased by {company_name}, the employee, or a third party.

## 3. General Use and Ownership
1. Users should be aware that the data they create on the corporate systems remains the property of {company_name}.
2. Employees are responsible for exercising good judgment regarding the reasonableness of personal use.

## 4. Unacceptable Use
The following activities are, in general, prohibited:
- Introduction of malicious programs into the network or server.
- Revealing your account password to others or allowing use of your account by others.
- Using a {company_name} computing asset to actively engage in procuring or transmitting material that is in violation of sexual harassment or hostile workplace laws in the user's local jurisdiction.
"""

    def _generate_itp(self, company_name: str, industry: str) -> str:
        return f"""# Insider Threat Program Policy
**Organization:** {company_name}
**Industry Sector:** {industry}

## 1. Overview
Insider threats pose a significant risk to {company_name}'s intellectual property, reputation, and operational continuity. This policy establishes the framework for preventing, detecting, and responding to insider risks.

## 2. Objectives
- safeguard critical assets.
- Promote a culture of security awareness.
- Respect privacy and civil liberties while monitoring for risk.

## 3. Roles and Responsibilities
- **Insider Threat Working Group:** Responsible for oversight.
- **HR/Legal:** ensuring compliance with labor laws.
- **Employees:** Reporting anomalous behavior.

## 4. Monitoring & Privacy
{company_name} reserves the right to monitor communications and system usage to ensuring the security of its data, consistent with applicable laws in the jurisdiction of operation.
"""
