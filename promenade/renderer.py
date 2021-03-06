from . import logging
import base64
import io
import jinja2
import os
import pkg_resources
import yaml

__all__ = ['Renderer']


LOG = logging.getLogger(__name__)


class Renderer:
    def __init__(self, *, config, target_dir):
        self.config = config
        self.target_dir = target_dir

    def render_generate_files(self):
        self.render_template_dir('generate')

    def render(self):
        for template_dir in self.config['Node']['templates']:
            self.render_template_dir(template_dir)

    def render_template_dir(self, template_dir):
        source_root = pkg_resources.resource_filename(
                'promenade', os.path.join('templates', template_dir))
        LOG.debug('Searching for templates in: "%s"', source_root)
        for root, _dirnames, filenames in os.walk(source_root,
                                                  followlinks=True):
            for source_filename in filenames:
                source_path = os.path.join(root, source_filename)
                self.render_template_file(path=source_path,
                                          root=source_root)

    def render_template_file(self, *, path, root):
        base_path = os.path.relpath(path, root)
        target_path = os.path.join(self.target_dir, base_path)

        _ensure_path(target_path)

        LOG.debug('Templating "%s" into "%s"', path, target_path)

        env = jinja2.Environment(
                loader=jinja2.PackageLoader('promenade', 'templates/include'),
                undefined=jinja2.StrictUndefined)
        env.filters['b64enc'] = _base64_encode
        env.filters['yaml_safe_dump_all'] = _yaml_safe_dump_all

        with open(path) as f:
            template = env.from_string(f.read())
        rendered_data = template.render(config=self.config)

        with open(target_path, 'w') as f:
            f.write(rendered_data)

        LOG.info('Installed "%s"', os.path.join('/', base_path))


def _ensure_path(path):
    base = os.path.dirname(path)
    os.makedirs(base, mode=0o775, exist_ok=True)


def _base64_encode(s):
    return base64.b64encode(s.encode()).decode()


def _yaml_safe_dump_all(documents):
    f = io.StringIO()
    yaml.safe_dump_all(documents, f)
    return f.getvalue()
