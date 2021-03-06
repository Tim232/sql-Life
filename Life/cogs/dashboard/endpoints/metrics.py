"""
Life
Copyright (C) 2020 MrRandom#9258

Life is free software: you can redistribute it and/or modify it under the terms of the GNU Affero General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later version.

Life is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE.  See the GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License along with Life. If not, see <https://www.gnu.org/licenses/>.
"""

from abc import ABC

from cogs.dashboard.utilities.bases import BaseHTTPHandler
import prometheus_client


class Metrics(BaseHTTPHandler, ABC):

    async def get(self):

        self.set_header(name='Content-Type', value=prometheus_client.CONTENT_TYPE_LATEST)
        return await self.finish(prometheus_client.generate_latest(prometheus_client.REGISTRY))


def setup(**kwargs):
    return [(r'/metrics', Metrics, kwargs)]



