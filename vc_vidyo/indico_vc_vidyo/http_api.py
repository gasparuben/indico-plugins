# This file is part of Indico.
# Copyright (C) 2002 - 2016 European Organization for Nuclear Research (CERN).
#
# Indico is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3 of the
# License, or (at your option) any later version.
#
# Indico is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Indico; if not, see <http://www.gnu.org/licenses/>.

from flask import request

from indico.web.http_api.hooks.base import HTTPAPIHook
from indico.modules.vc.models.vc_rooms import VCRoom, VCRoomStatus


class VCRoomCleanUpAPI(HTTPAPIHook):
    PREFIX = 'api'
    TYPES = ('deletevcroom', )
    RE = r'vidyo'
    GUEST_ALLOWED = False
    VALID_FORMATS = ('json', )
    COMMIT = True
    HTTP_POST = True

    # Just let the first 10 to be deleted
    MAX_COUNT = 10

    def _hasAccess(self, aw):
        from indico_vc_vidyo.plugin import VidyoPlugin
        return aw.getUser().user in VidyoPlugin.settings.acls.get('managers')

    def _getParams(self):
        super(VCRoomCleanUpAPI, self)._getParams()
        self._room_ids = request.form.getlist('room_id')

    def api_deletevcroom(self, aw):
        from indico_vc_vidyo.plugin import VidyoPlugin
        success = []
        failed = []
        notexist_at_indico = []

        counter = 0
        for id in self._room_ids:
            if counter > self.MAX_COUNT:
                break
            room = VCRoom.query.filter(VCRoom.type == 'vidyo',
                                       VCRoom.status == VCRoomStatus.created,
                                       VCRoom.data.contains({'vidyo_id': str(id)})).first()
            if not room:
                notexist_at_indico.append(id)
                continue
            try:
                room.plugin.delete_room(room, None)
            except:
                failed.append(room.data['vidyo_id'])
                VidyoPlugin.logger.exception('Could not delete VC room %s', room)
            else:
                counter += 1
                room.status = VCRoomStatus.deleted
                success.append(room.data['vidyo_id'])
                VidyoPlugin.logger.info('{} deleted', room)

        return {'success': '{}'.format(success),
                'failed': '{}'.format(failed),
                'notexist_at_indico': '{}'.format(notexist_at_indico)
                }
