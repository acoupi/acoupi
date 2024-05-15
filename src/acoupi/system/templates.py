"""Jinja2 environment for rendering templates."""

from jinja2 import Environment, PackageLoader, select_autoescape

__all__ = [
    "render_template",
]


env = Environment(
    loader=PackageLoader("acoupi"),
    autoescape=select_autoescape(),
)


def render_template(template_name, **kwargs):
    """Render a template with the given name and keyword arguments."""
    template = env.get_template(template_name)
    return template.render(**kwargs)
