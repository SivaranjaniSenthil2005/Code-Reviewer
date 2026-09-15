"""Knowledge base loader for security standards, anti-patterns, and style rules."""

from dataclasses import dataclass
from typing import List


@dataclass
class KnowledgeDocument:
    """A raw knowledge source document."""
    doc_id: str
    title: str
    category: str  # "security" | "bug" | "quality"
    language: str  # "all" | "python" | "javascript" | "typescript" | etc.
    content: str


# Curated starter knowledge base
DEFAULT_KNOWLEDGE_BASE: List[KnowledgeDocument] = [
    KnowledgeDocument(
        doc_id="sec-owasp-sqli",
        title="OWASP SQL Injection Prevention (CWE-89)",
        category="security",
        language="all",
        content="""# OWASP SQL Injection Prevention (CWE-89)
## Vulnerability Description
SQL injection occurs when untrusted user input is directly concatenated or formatted into dynamic SQL queries without parameterized placeholders.
## Risk
Attackers can bypass authentication, read, modify, or delete database tables, or execute administrative operations.
## Prevention & Remediation
1. Always use parameterized queries / prepared statements (e.g. `cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))`).
2. Use ORM queries that safely bind parameters.
3. Never use f-strings or string formatting (`%`, `.format()`) to construct SQL queries.
""",
    ),
    KnowledgeDocument(
        doc_id="sec-owasp-secrets",
        title="OWASP Hardcoded Secrets & Credentials (CWE-798)",
        category="security",
        language="all",
        content="""# OWASP Hardcoded Secrets (CWE-798)
## Vulnerability Description
Hardcoding passwords, API tokens, database URIs, or private keys directly in source code allows anyone with repository access to compromise systems.
## Prevention & Remediation
1. Read secrets from environment variables (e.g., `os.environ.get("API_KEY")` or `pydantic-settings`).
2. Store production secrets in a dedicated vault or secrets manager.
3. Add `.env` and sensitive files to `.gitignore`.
""",
    ),
    KnowledgeDocument(
        doc_id="sec-owasp-xss",
        title="OWASP Cross-Site Scripting (XSS) (CWE-79)",
        category="security",
        language="javascript",
        content="""# Cross-Site Scripting (XSS) Prevention
## Vulnerability Description
Rendering unsanitized user input into HTML DOM elements (such as `dangerouslySetInnerHTML` in React or `.innerHTML` in DOM APIs) allows malicious script execution.
## Prevention & Remediation
1. Use safe text rendering properties (`textContent` or React `{variable}` JSX bindings).
2. Use DOMPurify before inserting sanitized HTML when HTML rendering is strictly necessary.
""",
    ),
    KnowledgeDocument(
        doc_id="bug-python-mutable-defaults",
        title="Python Mutable Default Arguments",
        category="bug",
        language="python",
        content="""# Python Mutable Default Arguments Anti-Pattern
## Description
Using a mutable object (e.g. `def add_item(item, list_target=[])`) as a default argument creates a shared list across all function invocations because default arguments are evaluated once at function definition time.
## Prevention
Use `None` as the default value:
`def add_item(item, list_target=None): if list_target is None: list_target = []`
""",
    ),
    KnowledgeDocument(
        doc_id="bug-resource-leak",
        title="Resource Leaks: Unclosed Files and Connections",
        category="bug",
        language="all",
        content="""# Unclosed Resource Leaks
## Description
Failing to close file descriptors, database connections, or HTTP sessions causes file descriptor exhaustion and memory leaks.
## Prevention
Use language context managers (e.g. `with open(...) as f:` in Python, `try-with-resources` in Java, or `using` statements in C#).
""",
    ),
    KnowledgeDocument(
        doc_id="quality-python-pep8",
        title="Python Clean Code & PEP 8 Style Rules",
        category="quality",
        language="python",
        content="""# Python Clean Code & PEP 8 Standards
## Rules
1. Function and variable names should follow `snake_case`.
2. Class names should follow `PascalCase`.
3. Constants should follow `UPPER_SNAKE_CASE`.
4. Keep cyclomatic complexity low by splitting nested conditionals and large functions into smaller helper functions.
5. Provide explicit type annotations for function signatures.
""",
    ),
]


def load_starter_knowledge_base() -> List[KnowledgeDocument]:
    """Load the starter knowledge base documents."""
    return DEFAULT_KNOWLEDGE_BASE
