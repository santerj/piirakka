from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATE_DIR = Path(__file__).resolve().parents[1] / "templates"
env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)), autoescape=select_autoescape())


def render(component: str, **kwargs) -> str:
    """
    Render a Jinja component into html.

    Args:
    -------
    component: path to component, from the base directory piirakka/templates/
    data: the relevant data needed for component.

    """
    template = env.get_template(component)
    return template.render(**kwargs)
