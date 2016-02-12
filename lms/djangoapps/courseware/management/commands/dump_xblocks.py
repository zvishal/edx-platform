# pylint: disable=missing-docstring

from textwrap import dedent

from django.core.management.base import BaseCommand, CommandError
from xblock.core import XBlock
from xblock.fields import Scope
import yaml


class Command(BaseCommand):
    """
    Produce a YAML description of all XBlocks the platform knows about and their fields.
    """
    help = dedent(__doc__).strip()
    option_list = BaseCommand.option_list

    def handle(self, *args, **options):
        blocks = {}
        for block_type, block_class in XBlock.load_classes():
            block_struct = blocks.setdefault(block_type, {})
            block_struct['fields'] = []
            if getattr(block_class, 'has_children', False):
                block_struct['has_children'] = True
            for field_name, field in block_class.fields.items():
                if field_name == 'xml_attributes':
                    continue
                if field.scope == Scope.settings:
                    block_struct['fields'].append(field_name)

        return yaml.dump(blocks, default_flow_style=False)
