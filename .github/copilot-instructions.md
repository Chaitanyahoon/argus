- [x] Verify that the copilot-instructions.md file in the .github directory is created.

- [x] Clarify Project Requirements
	Project type: Discord bot, Language: Python, Frameworks: discord.py, Gemini AI

- [x] Scaffold the Project
	Project structure created with bot.py, cogs/, core/, config management

- [x] Customize the Project
	Codebase modified to remove unwanted features (admin, moderation, leveling, music, tickets, welcome, temp voice), keeping only voice AI and therapy features

- [x] Install Required Extensions
	No extensions needed for this Python Discord bot project

- [x] Compile the Project
	Python project - no compilation needed, dependencies installed via pip

- [x] Create and Run Task
	No VS Code tasks needed - bot runs with `python bot.py`

- [x] Launch the Project
	Bot can be launched with `python bot.py` after configuring .env file

- [x] Ensure Documentation is Complete
	README.md and CONTRIBUTING.md updated to reflect current features, copilot-instructions.md cleaned up

## Execution Guidelines
PROGRESS TRACKING:
- Track progress through the above checklist.
- Mark steps as completed with [x] and add summaries.
- Read current todo list status before starting each new step.

COMMUNICATION RULES:
- Avoid verbose explanations or printing full command outputs.
- If a step is skipped, state that briefly (e.g. "No extensions needed").
- Do not explain project structure unless asked.
- Keep explanations concise and focused.

DEVELOPMENT RULES:
- Use '.' as the working directory unless user specifies otherwise.
- Avoid adding media or external links unless explicitly requested.
- Use placeholders only with a note that they should be replaced.
- Use VS Code API tool only for VS Code extension projects.
- Once the project is created, it is already opened in Visual Studio Code—do not suggest commands to open this project in Visual Studio again.
- If the project setup information has additional rules, follow them strictly.

FOLDER CREATION RULES:
- Always use the current directory as the project root.
- If you are running any terminal commands, use the '.' argument to ensure that the current working directory is used ALWAYS.
- Do not create a new folder unless the user explicitly requests it besides a .vscode folder for a tasks.json file.
- If any of the scaffolding commands mention that the folder name is not correct, let the user know to create a new folder with the correct name and then reopen it again in vscode.

EXTENSION INSTALLATION RULES:
- Only install extension specified by the get_project_setup_info tool. DO NOT INSTALL any other extensions.

PROJECT CONTENT RULES:
- If the user has not specified project details, assume they want a "Hello World" project as a starting point.
- Avoid adding links of any type (URLs, files, folders, etc.) or integrations that are not explicitly required.
- Avoid generating images, videos, or any other media files unless explicitly requested.
- If you need to use any media assets as placeholders, let the user know that these are placeholders and should be replaced with the actual assets later.
- Ensure all generated components serve a clear purpose within the user's requested workflow.
- If a feature is assumed but not confirmed, prompt the user for clarification before including it.
- If you are working on a VS Code extension, use the VS Code API tool with a query to find relevant VS Code API references and samples related to that query.

TASK COMPLETION RULES:
- Your task is complete when:
  - Project is successfully scaffolded and compiled without errors
  - copilot-instructions.md file in the .github directory exists in the project
  - README.md file exists and is up to date
  - User is provided with clear instructions to debug/launch the project

- Work through each checklist item systematically.
- Keep communication concise and focused.
- Follow development best practices.
