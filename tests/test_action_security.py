import re
from pathlib import Path

def test_action_yml_does_not_interpolate_inputs_in_run_script():
    action_file = Path("action.yml")
    assert action_file.exists(), "action.yml must exist"

    content = action_file.read_text(encoding="utf-8")

    # Locate the run block
    run_match = re.search(r"run:\s*\|\s*(.*)", content, re.DOTALL)
    assert run_match, "action.yml must have a run: block"
    run_block = run_match.group(1)

    # Verify no ${{ inputs... }} interpolation in the run body
    assert "${{ inputs." not in run_block, (
        "action.yml should not interpolate ${{ inputs... }} directly into run script "
        "to prevent shell command injection. Pass them via env: instead."
    )

    # Verify inputs are passed via env
    assert "INPUT_PATH: ${{ inputs.path }}" in content
    assert "INPUT_FORMAT: ${{ inputs.format }}" in content
    assert "INPUT_FAIL_ON: ${{ inputs.fail-on }}" in content

    # Verify the shell script quotes the environment variables
    assert '"$INPUT_PATH"' in run_block
    assert '"$INPUT_FORMAT"' in run_block
    assert '"$INPUT_FAIL_ON"' in run_block

def test_readme_action_example_matches_repository():
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "uses: aliasnull/RepoMedic@v0.1.1" in readme
    assert "https://github.com/aliasnull/RepoMedic" in readme
    assert "your-org" not in readme
