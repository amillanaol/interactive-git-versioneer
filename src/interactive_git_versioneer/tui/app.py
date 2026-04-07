"""
Interactive Git Versioneer - TUI Application
Lazygit-style interface for semantic versioning
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, ListView, ListItem


class VersioneerApp(App):
    """TUI Application for Interactive Git Versioneer"""

    CSS_PATH = "styles.tcss"
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("1", "focus_status", "Status"),
        ("2", "focus_files", "Files"),
        ("3", "focus_branches", "Branches"),
        ("4", "focus_commits", "Commits"),
        ("tab", "focus_next", "Next Panel"),
        ("shift+tab", "focus_prev", "Prev Panel"),
        ("?", "toggle_help", "Help"),
        ("enter", "action_enter", "Execute"),
        ("space", "action_toggle", "Toggle"),
        ("n", "action_new", "New"),
        ("d", "action_diff", "Diff"),
        ("r", "action_refresh", "Refresh"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.repo = None
        self.current_version = "0.0.0"
        self.next_version = "0.1.0"
        self.release_type = "minor"
        self.untagged_commits = []
        self.local_branches = []
        self.remote_branches = []
        self.local_tags = []
        self.modified_files = []

    def load_repo_data(self):
        """Load repository data into the app"""
        try:
            from ..core.git_ops import (
                get_git_repo,
                get_last_tag,
                get_untagged_commits,
                get_next_version,
                parse_version,
            )
            from ..tags.tagger import parse_version as parse_v

            self.repo = get_git_repo()

            # Get last tag and version info
            last_tag = get_last_tag(self.repo)
            if last_tag:
                self.current_version = last_tag
                # Determine release type from commits
                self.untagged_commits = get_untagged_commits(self.repo)
                if self.untagged_commits:
                    # Analyze commits to guess release type
                    types = {"major": 0, "minor": 0, "patch": 0}
                    for commit in self.untagged_commits:
                        msg = commit.message.lower()
                        if "feat" in msg or "major" in msg:
                            types["major"] += 1
                        elif "fix" in msg or "refactor" in msg:
                            types["minor"] += 1
                        else:
                            types["patch"] += 1

                    if types["major"] > 0:
                        self.release_type = "major"
                    elif types["minor"] > 0:
                        self.release_type = "minor"
                    else:
                        self.release_type = "patch"

                    self.next_version = get_next_version(self.repo, self.release_type)
                else:
                    self.next_version = last_tag
                    self.release_type = "none"
            else:
                self.current_version = "0.0.0"
                self.next_version = "0.1.0"
                self.untagged_commits = get_untagged_commits(self.repo)

            # Get branches
            self.local_branches = [b.name for b in self.repo.branches]

            # Get remote branches
            try:
                for remote in self.repo.remotes:
                    self.remote_branches.extend([ref.name for ref in remote.refs])
            except Exception:
                pass

            # Get tags
            self.local_tags = sorted(
                [t.name for t in self.repo.tags], key=lambda x: parse_v(x), reverse=True
            )

            # Get modified files
            try:
                status = self.repo.git.status("--porcelain")
                self.modified_files = []
                for line in status.split("\n"):
                    if line.strip():
                        if line.startswith("??"):
                            self.modified_files.append(("untracked", line[3:]))
                        elif line.startswith(" M") or line.startswith("M "):
                            self.modified_files.append(("modified", line[3:]))
                        elif line.startswith(" D") or line.startswith("D "):
                            self.modified_files.append(("deleted", line[3:]))
                        elif line.startswith(" A") or line.startswith("A "):
                            self.modified_files.append(("added", line[3:]))
                        else:
                            self.modified_files.append(("staged", line[3:]))
            except Exception:
                pass

        except Exception as e:
            self.repo = None

    def compose(self) -> ComposeResult:
        yield Header()

        with Vertical(id="main-container"):
            yield StatusPanel(id="status-panel")

            with Horizontal(id="middle-row"):
                yield FilesPanel(id="files-panel")
                yield BranchesPanel(id="branches-panel")

            yield CommitsPanel(id="commits-panel")

            with Horizontal(id="bottom-row"):
                yield LogPanel(id="log-panel")
                yield OutputPanel(id="output-panel")

        yield Footer()

    def on_mount(self):
        """Called when app is mounted - load data here"""
        self.load_repo_data()
        self.update_panels()

    def update_panels(self):
        """Update all panels with current data"""
        # Update status panel
        status_panel = self.query_one("#status-panel", StatusPanel)
        status_panel.update_content(
            self.current_version,
            self.next_version,
            self.release_type,
            len(self.untagged_commits),
        )

        # Update files panel - now shows untagged commits + tags
        files_panel = self.query_one("#files-panel", FilesPanel)
        files_panel.update_content(self.untagged_commits, self.local_tags)

        # Update branches panel
        branches_panel = self.query_one("#branches-panel", BranchesPanel)
        branches_panel.update_content(self.local_branches, self.local_tags)

        # Update commits panel
        commits_panel = self.query_one("#commits-panel", CommitsPanel)
        commits_panel.update_content(self.untagged_commits)

    def action_focus_status(self):
        self.query_one("#status-panel", StatusPanel).focus()

    def action_focus_files(self):
        self.query_one("#files-panel", FilesPanel).focus()

    def action_focus_branches(self):
        self.query_one("#branches-panel", BranchesPanel).focus()

    def action_focus_commits(self):
        self.query_one("#commits-panel", CommitsPanel).focus()

    def action_focus_next(self):
        self.screen.focus_next()

    def action_focus_prev(self):
        self.screen.focus_previous()

    def action_refresh(self):
        """Refresh all data"""
        self.load_repo_data()
        self.update_panels()

    def action_enter(self):
        pass

    def action_toggle(self):
        pass

    def action_new(self):
        pass

    def action_diff(self):
        pass


class StatusPanel(Static):
    """Panel [1] - Shows current version and next version prediction"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_version = "0.0.0"
        self.next_version = "0.1.0"
        self.release_type = "minor"
        self.pending_count = 0

    def compose(self) -> ComposeResult:
        yield Static("", id="status-content")

    def update_content(self, current, next_ver, release_type, pending):
        self.current_version = current
        self.next_version = next_ver
        self.release_type = release_type
        self.pending_count = pending

        # Format: Current: v1.2.3 → Next: v1.3.0 (minor) | 5 commits pending
        type_indicator = {
            "major": "[red]▲[/red] major",
            "minor": "[green]▶[/green] minor",
            "patch": "[yellow]●[/yellow] patch",
            "none": "[dim]✓[/dim] up to date",
        }.get(release_type, release_type)

        pending_text = (
            f"[yellow]{pending} commit(s) pending[/yellow]"
            if pending > 0
            else "[green]✓ up to date[/green]"
        )

        content = f"[bold]Interactive Git Versioneer[/bold]  |  Current: [cyan]{current}[/cyan]  →  Next: [purple]{next_ver}[/purple] ({type_indicator})  |  {pending_text}"
        self.query_one("#status-content", Static).update(content)


class FilesPanel(Static):
    """Panel [2] - Shows untagged commits"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.commits = []
        self.tags = []

    def compose(self) -> ComposeResult:
        yield Static("Commits", id="files-content")

    def update_content(self, commits, tags):
        self.commits = commits
        self.tags = tags
        content_lines = ["[bold]Commits Without Tags[/bold]"]

        if not commits:
            content_lines.append("[dim]All commits are tagged[/dim]")
        else:
            for commit in commits:
                msg = commit.message
                type_icon = "[cyan]●[/cyan]"
                if msg.startswith("feat"):
                    type_icon = "[green]+[/green]"
                elif msg.startswith("fix"):
                    type_icon = "[red]●[/red]"
                elif msg.startswith("docs"):
                    type_icon = "[blue]◆[/blue]"
                elif msg.startswith("refactor"):
                    type_icon = "[purple]◐[/purple]"

                display_msg = msg[:40] + "..." if len(msg) > 40 else msg
                content_lines.append(
                    f"  {type_icon}  [{commit.hash[:7]}] {display_msg}"
                )

        # Show last 5 tags
        content_lines.append(f"\n[bold]Tags ({len(tags)})[/bold]")
        for tag in tags[:5]:
            content_lines.append(f"  [purple]{tag}[/purple]")
        if len(tags) > 5:
            content_lines.append(f"  [dim]... and {len(tags) - 5} more[/dim]")

        self.query_one("#files-content", Static).update("\n".join(content_lines))


class BranchesPanel(Static):
    """Panel [3] - Shows changelogs"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.changelogs = []

    def compose(self) -> ComposeResult:
        yield Static("Changelogs", id="branches-content")

    def update_content(self, branches, tags):
        import os
        from ..core.git_ops import get_git_repo

        content_lines = ["[bold]Changelogs[/bold]"]

        try:
            repo = get_git_repo()
            repo_root = repo.working_dir

            # Check for CHANGELOG.md
            changelog_path = os.path.join(repo_root, "CHANGELOG.md")
            if os.path.exists(changelog_path):
                with open(changelog_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Extract versions from changelog
                import re

                versions = re.findall(r"##\s*\[([^\]]+)\]", content)

                if versions:
                    content_lines.append(f"\n[bold]Recent Versions[/bold]")
                    for version in versions[:8]:
                        if version in [t.name for t in repo.tags]:
                            content_lines.append(
                                f"  [purple]{version}[/purple] [green]✓[/green]"
                            )
                        else:
                            content_lines.append(f"  [purple]{version}[/purple]")
                else:
                    content_lines.append("[dim]No versions found[/dim]")
            else:
                content_lines.append("[dim]CHANGELOG.md not found[/dim]")

            # Also show tags as they're related
            content_lines.append(f"\n[bold]Tags ({len(tags)})[/bold]")
            for tag in tags[:5]:
                content_lines.append(f"  [purple]{tag}[/purple]")
            if len(tags) > 5:
                content_lines.append(f"  [dim]... and {len(tags) - 5} more[/dim]")

        except Exception as e:
            content_lines.append(f"[red]Error: {str(e)[:30]}[/red]")

        self.query_one("#branches-content", Static).update("\n".join(content_lines))


class CommitsPanel(Static):
    """Panel [4] - Shows releases"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.releases = []

    def compose(self) -> ComposeResult:
        yield Static("Releases", id="commits-content")

    def update_content(self, commits):
        from ..core.git_ops import get_git_repo
        from ..releases.gh_releases import get_releases

        content_lines = ["[bold]Releases[/bold]"]

        try:
            repo = get_git_repo()

            # Get remote releases (GitHub)
            try:
                releases, error = get_releases(limit=10)

                if error:
                    content_lines.append(f"[yellow]GitHub: {error}[/yellow]")
                elif releases:
                    for release in releases:
                        tag = release.get("tag", release.get("tag_name", "unknown"))
                        date = release.get("date", release.get("published_at", ""))[:10]

                        if date:
                            content_lines.append(
                                f"  [purple]{tag}[/purple] [dim]{date}[/dim]"
                            )
                        else:
                            content_lines.append(f"  [purple]{tag}[/purple]")
                else:
                    content_lines.append("[dim]No GitHub releases found[/dim]")

            except Exception as e:
                content_lines.append(f"[yellow]GitHub not configured[/yellow]")
                content_lines.append(f"[dim]{str(e)[:40]}[/dim]")

        except Exception as e:
            content_lines.append(f"[red]Error: {str(e)[:40]}[/red]")

        self.query_one("#commits-content", Static).update("\n".join(content_lines))


class LogPanel(Static):
    """Panel [5a] - Command log"""

    def compose(self) -> ComposeResult:
        yield Static("Command Log", id="log-content")


class OutputPanel(Static):
    """Panel [5b] - Git output"""

    def compose(self) -> ComposeResult:
        yield Static("Git Output", id="output-content")


def run_tui():
    """Entry point for TUI application"""
    app = VersioneerApp()
    app.run()


if __name__ == "__main__":
    run_tui()
