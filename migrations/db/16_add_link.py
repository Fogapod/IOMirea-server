"""
IOMirea-server - A server for IOMirea messenger
Copyright (C) 2019  Eugene Ershov

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""


from migration import DBMigration


class Migration(DBMigration):
    async def up(self, latest: int) -> None:
        await self.conn.fetch(
            """
            ALTER TABLE messages ADD CONSTRAINT messages_channelid_fkey FOREIGN KEY (channel_id) REFERENCES channels(id);
			ALTER TABLE messages ADD CONSTRAINT messages_authorid_fkey FOREIGN KEY (author_id) REFERENCES users(id);
			
			ALTER TABLE users ADD CONSTRAINT users_channelids_fkey FOREIGN KEY (channel_ids) REFERENCES channels(id);
			ALTER TABLE users ADD CONSTRAINT users_lastreadmessageids_fkey FOREIGN KEY (last_read_message_ids) REFERENCES messages(id);
			
			ALTER TABLE channels ADD CONSTRAINT channels_userids_fkey FOREIGN KEY (user_ids) REFERENCES users(id);
			ALTER TABLE channels ADD CONSTRAINT channels_pinnedids_fkey FOREIGN KEY (pinned_ids) REFERENCES messages(id);
			
			ALTER TABLE files ADD CONSTRAINT files_channelid_fkey FOREIGN KEY (channel_id) REFERENCES channels(id);
			ALTER TABLE files ADD CONSTRAINT files_messageid_fkey FOREIGN KEY (message_id) REFERENCES messages(id);
			
			ALTER TABLE bugreports ADD CONSTRAINT bugreports_userid_fkey FOREIGN KEY (user_id) REFERENCES users(id);
			
			ALTER TABLE tokens ADD CONSTRAINT tokens_userid_fkey FOREIGN KEY (user_id) REFERENCES users(id);
			ALTER TABLE tokens ADD CONSTRAINT tokens_appid_fkey FOREIGN KEY (app_id) REFERENCES applications(id) ON DELETE CASCADE;
            """
        )
