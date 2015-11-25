"""
Stub implementation of programs service for acceptance tests
"""

import re
import urlparse
from .http import StubHttpRequestHandler, StubHttpService


class StubProgramsServiceHandler(StubHttpRequestHandler):

    @property
    def _params(self):
        return urlparse.parse_qs(urlparse.urlparse(self.path).query)

    def do_GET(self):
        pattern_handlers = {
            "/api/v1/programs/$": self.get_programs_list,
        }
        if self.match_pattern(pattern_handlers):
            return
        self.send_response(404, content="404 Not Found")

    def match_pattern(self, pattern_handlers):
        path = urlparse.urlparse(self.path).path
        for pattern in pattern_handlers:
            match = re.match(pattern, path)
            if match:
                pattern_handlers[pattern](**match.groupdict())
                return True
        return None

    def get_programs_list(self):
        programs = self.server.config.get('programs', [])
        self.send_json_response(programs)


class StubProgramsService(StubHttpService):
    HANDLER_CLASS = StubProgramsServiceHandler
