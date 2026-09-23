# crm/management/commands/runmcp.py
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run the MCP server over stdio so Claude Desktop/Code can read and add contacts."

    def handle(self, *args, **options):
        # Django is already configured here; importing the server registers the
        # tools against the same models the app uses. stdout is reserved for the
        # MCP protocol, so status goes to stderr.
        from mcp_server.server import mcp

        self.stderr.write("Starting pipeline MCP server (stdio)...")
        mcp.run(transport="stdio")
