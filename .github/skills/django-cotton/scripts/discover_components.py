#!/usr/bin/env python
"""Discover all available Django Cotton components in the project.

This script finds all Cotton components from:
- Project-level templates/cotton/ directory
- Third-party packages (e.g., django-cotton-bs5, django-mvp)
- App-level component directories

Usage:
    uv run python manage.py shell < .github/skills/django-cotton/scripts/discover_components.py

Or from within Django shell:
    from pathlib import Path
    exec(open('.github/skills/django-cotton/scripts/discover_components.py').read())
"""

from pathlib import Path

from django.conf import settings
from django.template import engines


def discover_cotton_components() -> list[str]:
    """Discover all available Cotton components in the Django project.

    Returns:
        Component names in kebab-case, sorted.
    """
    cotton_dir = getattr(settings, "COTTON_DIR", "cotton")

    try:
        engine = engines["django"]
    except KeyError:
        print("Error: Django template engine not found")
        return []

    components = set()
    for loader in engine.engine.template_loaders:
        if hasattr(loader, "get_dirs"):
            for template_dir in loader.get_dirs():
                cotton_path = Path(template_dir) / cotton_dir

                if cotton_path.exists() and cotton_path.is_dir():
                    for html_file in cotton_path.rglob("*.html"):
                        rel_path = html_file.relative_to(cotton_path)
                        component_path = rel_path.with_suffix("")

                        # Handle both Windows and Unix path separators
                        component_name = (
                            str(component_path).replace("\\", ".").replace("/", ".")
                        )

                        component_name = component_name.replace("_", "-")

                        # An index.html is the component named by its parent folder
                        if component_name.endswith(".index"):
                            component_name = component_name.rsplit(".", 1)[0]

                        components.add(component_name)

    return sorted(components)


def print_components(components: list[str], format: str = "list") -> None:
    """Print components in one of several formats.

    Args:
        components: Component names, as returned by `discover_cotton_components`.
        format: Output format: 'list', 'usage', or 'grouped'.
    """
    if not components:
        print("No Cotton components found.")
        return

    print(f"\n{'='*60}")
    print(f"Found {len(components)} Cotton components:")
    print(f"{'='*60}\n")

    if format == "list":
        for comp in components:
            print(f"  {comp}")

    elif format == "usage":
        for comp in components:
            print(f"  <c-{comp} />")

    elif format == "grouped":
        from collections import defaultdict

        grouped = defaultdict(list)

        for comp in components:
            if "." in comp:
                namespace = comp.split(".")[0]
                grouped[namespace].append(comp)
            else:
                grouped["(root)"].append(comp)

        for namespace in sorted(grouped.keys()):
            print(f"\n{namespace}:")
            for comp in grouped[namespace]:
                print(f"  <c-{comp} />")

    print(f"\n{'='*60}\n")


if __name__ == "__main__" or "__file__" not in locals():
    components = discover_cotton_components()

    # You can change the format here: 'list', 'usage', or 'grouped'
    print_components(components, format="grouped")

    print("Components list is available as 'components' variable")
    print("Usage: print(components)")
