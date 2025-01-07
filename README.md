# telegram_bot

Telegram bot for a local LGBT+ group.

This bot posts useful information to the group's chat when asked.

## Commands

### /rules
- **Private Chat**: Posts a list of rules with a short summary and buttons to read the full rules.
- **Group Chat**: Posts the list of rules with short summaries without any buttons.

### /rulesadmin
- **Private Chat (Admins Only)**: Posts a list of rules with summaries. Admins can select which rule they want to post to the group in full.

### /postrule <1-6>
- **Group Chat (Admins Only)**: Posts a specific rule by its number. Useful when the admin knows the rule number they wish to post.

### /links
- Posts useful links found in the chat's description.

### /admins
- (In Progress) Will provide information about the admins, likely restricted to private chats.

## Future Ideas
- Restrict group information access to users in the group chat.
- Add inline commands such as:
  - `@<bot_name> groupinfo`: Posts a short description of the group.
  - `@<bot_name> joinlink`: Posts the link to start the process of joining the group.
- Add a command `/botlist` to list the bots associated with the group and their functions.
- Store verified members' ages and allow them to use the command `/joinchat` to get a link to rejoin the group chat.