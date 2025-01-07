# Telegram Bot

A Telegram bot designed for a local LGBT+ group to provide useful information and enhance group interactions.

---
## Features

- **Rules Management:** Share and manage group rules with ease.
- **Admin Tools:** Streamline admin functionalities like posting rules and managing group information.
- **Useful Links:** Provide quick access to important links related to the group.
- **Future Enhancements:** Inline commands, verified member tools, and more.

---
## Configuration

The bot requires specific configuration and data files to function properly.

### Configuration File
The configuration file (`src/config/config.py`) should include:

```python
# The bot's Telegram bot token
token = "YOUR_BOT_TOKEN"

# The group's chat ID
group_chat_id = -123456789
```

### Data File
The data file (`src/data/data.py`) should include details about roles, rules, and more.

#### Example Data Structure:

```python
# Roles of the admins
roles = {
    "ROLE_NAME_1": {
        "summary": "Short summary of the role.",
        "description": "Detailed description of the role.",
        "admins": [
            {"name": "Admin1", "username": "username1"},
            {"name": "Admin2", "username": "username2"}
        ]
    },
    "ROLE_NAME_2": {
        "summary": "Short summary of the role.",
        "description": "Detailed description of the role.",
        "admins": [
            {"name": "Admin1", "username": "username1"},
            {"name": "Admin2", "username": "username2"}
        ]
    }
}

# Rules of the group
rules = {
    "rule_name_1": {
        "summary": "Short summary of the rule.",
        "description": "Detailed description of the rule."
    },
    "rule_name_2": {
        "summary": "Short summary of the rule.",
        "description": "Detailed description of the rule."
    }
}
```

---
## Commands

### General Commands

- **`/rules`**
  - **Private Chat:** Lists rules with summaries and buttons for detailed views.
  - **Group Chat:** Lists rules with summaries (no buttons).

- **`/links`**
  - Posts useful links found in the chat description.

- **`/admins`** *(In Progress)*
  - Will display admin details, likely restricted to private chats.

### Admin-Only Commands

- **`/rulesadmin`** *(Private Chat Only)*
  - Lists rules with summaries. Admins can select a rule to post in full.

- **`/postrule <1-6>`** *(Group Chat Only)*
  - Posts a specific rule by its number.

---
## Future Ideas

- Restrict information access to verified group members.
- Implement inline commands:
  - **`@<bot_name> groupinfo`**: Posts a short group description.
  - **`@<bot_name> joinlink`**: Provides the link to start the joining process.
- Add `/botlist` command to list group bots and their functions.
- Store verified member ages and allow rejoining the group with `/joinchat`.

---
## Getting Started

1. **Set up the configuration file:** Add your bot token and group chat ID.
2. **Prepare the data file:** Define roles, rules, and other group-specific details.
3. **Run the bot:** Start the bot and test its functionalities.

For more details, check the source files in the `src/` directory.

