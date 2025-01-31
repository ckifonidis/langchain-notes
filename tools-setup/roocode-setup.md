## Roo Code installation & configuration
1. Launch VS Code
2. On the left side navigation bar, click on the "Extensions" icon
3. Search for "GitHub Copilot" and install it
4. Once installation is complete, a copilot pane will open on the right side of the VS Code window. Next to the "Sign in to Use Copilot for Free" button, there is an arrow. Click it and select "Sign in with github.com account". 
5. A github login page will open in your browser. Follow the instructions in order to login to github and authorize VS Code to use your github account.
6. Once this is done, go back to the "Extensions" icon, search for "Roo Code" and install it.
8. A new icon that looks like a rocket, should show up on the left side navigation bar. Click on it.
9. Now you need to set up an API provider, that Roo Code is going to use. Let's set it up to use Github Copilot. In the "API Provider" dropdown, select "VS Code LM API". In the "Language Model" dropdown, select "Claude-3.5-sonnet".
10. In the next screen, check the "Auto-approve" checkbox, then click on the arrow next to it. Check the following options:
    - Read files and directories
    - Edit files
    - Retry failed requests
11. Now you will define a role that will shape the LLM's behavior and expertise, depending on the intended usage. A role is basically a type of prompt, which can instruct the LLM to act as a software engineer, a business analyst, a QA tester, etc.
    - First, click on the arrow next to the "Code" dropdown, at the bottom of the left-hand pane, and select "Edit...". Then, click on the "+" icon, in the "Mode-Specific Prompts" section.
    - Load the content of the "api_design_writer.md" file, copy and paste it into the "Role definition" textbox.
    - Type "API design writer" in the "Name" textbox.
    - Type "api-design-writer" in the "Slug" textbox.
    - Click on "Create Mode".