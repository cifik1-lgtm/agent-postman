"""
Agent Postman — Rich Terminal UI (upgraded main CLI)
Replaces plain ANSI with rich library for premium look.
"""
import sys, json, time
from agent_postman import inspector, tester, replayer, validator, simulator, tracer, store

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.live import Live
from rich.text import Text
from rich.prompt import Prompt, IntPrompt
from rich import box
from rich.columns import Columns
from rich.align import Align
from rich.rule import Rule

console = Console()

BANNER = """[bold cyan]
 ╔══════════════════════════════════════════════════════════╗
 ║   🔭  AGENT POSTMAN  —  Postman for AI Agents  v1.0.0   ║
 ║      Inspect · Test · Replay · Simulate · Trace          ║
 ╚══════════════════════════════════════════════════════════╝[/bold cyan]"""

def print_menu():
    console.print(Panel(
        "[green]1[/] · [bold]inspect[/]    Browse captured agent messages\n"
        "[green]2[/] · [bold]test[/]       Fire a request to an agent endpoint\n"
        "[green]3[/] · [bold]replay[/]     Replay a saved workflow\n"
        "[green]4[/] · [bold]simulate[/]   Simulate another agent / flood test\n"
        "[green]5[/] · [bold]validate[/]   Validate a payload against a schema\n"
        "[green]6[/] · [bold]trace[/]      Live-trace all agent traffic\n"
        "[green]7[/] · [bold]summary[/]    Traffic summary & health stats\n"
        "[green]8[/] · [bold]inject[/]     Manually inject a test message\n"
        "[red]q[/] · quit",
        title="[bold yellow]Commands[/]",
        border_style="dim",
        padding=(1, 2),
    ))


def _status_badge(s: str) -> Text:
    if s in ("ok", "valid"):    return Text(f"✓ {s}", style="bold green")
    if s in ("error", "invalid", "failed"): return Text(f"✗ {s}", style="bold red")
    if s == "sent":             return Text(f"→ {s}", style="bold blue")
    return Text(s, style="yellow")


def cmd_inspect():
    agent_filter = Prompt.ask("Filter by agent name", default="").strip() or None
    msgs = inspector.list_messages(filter_agent=agent_filter)
    if not msgs:
        console.print("[yellow]No messages found.[/]")
        return

    table = Table(box=box.ROUNDED, border_style="dim", show_lines=False)
    table.add_column("ID",   style="dim", width=5, justify="right")
    table.add_column("Time", style="dim", width=10)
    table.add_column("From", style="cyan", width=20)
    table.add_column("To",   style="magenta", width=38)
    table.add_column("MS",   style="yellow", width=7, justify="right")
    table.add_column("Status")

    for m in msgs:
        ts  = m.get("timestamp", "")[:19].replace("T", " ")[11:]
        frm = str(m.get("from", "?"))[:19]
        to  = str(m.get("to",   "?"))[:37]
        ms  = str(m.get("elapsed_ms", "—"))
        table.add_row(str(m.get("id","?")), ts, frm, to, ms, _status_badge(m.get("status","?")))

    console.print(table)

    detail_id = Prompt.ask("Enter ID to see full detail (blank=skip)", default="").strip()
    if detail_id.isdigit():
        msg = inspector.inspect(int(detail_id))
        if msg:
            console.print(Syntax(json.dumps(msg, indent=2), "json", theme="monokai"))


def cmd_test():
    url    = Prompt.ask("[cyan]Endpoint URL[/]")
    raw    = Prompt.ask("[cyan]JSON payload[/]", default="{}")
    method = Prompt.ask("[cyan]Method[/]", default="POST").upper()
    try:
        payload = json.loads(raw)
    except Exception:
        console.print("[red]Invalid JSON.[/]"); return

    with console.status("[bold cyan]Sending request...[/]"):
        result = tester.call_endpoint(url, payload, method=method)

    st = result.get("status","?")
    ms = result.get("elapsed_ms", "?")
    http_code = result.get("http_status", "?")
    badge = _status_badge(st)

    console.print(Panel(
        f"Status: {badge}   HTTP: [bold]{http_code}[/]   Time: [yellow]{ms}ms[/]\n\n"
        + Syntax(json.dumps(result.get("response",{}), indent=2), "json", theme="monokai").highlight(""),
        title="[bold]Response[/]",
        border_style="green" if st == "ok" else "red",
    ))


def cmd_validate():
    raw = Prompt.ask("[cyan]JSON payload to validate[/]")
    try:
        payload = json.loads(raw)
    except Exception:
        console.print("[red]Invalid JSON.[/]"); return

    console.print("[dim]Schema: 1) Tool call  2) Agent response  3) HTTP endpoint[/]")
    choice = Prompt.ask("Schema", default="1")
    schema = {
        "1": validator.AGENT_TOOL_CALL_SCHEMA,
        "2": validator.AGENT_RESPONSE_SCHEMA,
        "3": validator.HTTP_ENDPOINT_SCHEMA,
    }.get(choice, validator.AGENT_TOOL_CALL_SCHEMA)

    result = validator.validate(payload, schema)
    if result["valid"]:
        console.print(Panel("[bold green]✓ Payload is VALID[/]", border_style="green"))
    else:
        errs = "\n".join(f"• {e}" for e in result["errors"])
        console.print(Panel(f"[bold red]✗ Payload is INVALID[/]\n\n{errs}", border_style="red"))


def cmd_trace():
    console.print(Panel("[yellow]Live tracing started. Press Ctrl+C to stop.[/]",
                        border_style="yellow"))
    table = Table(box=box.SIMPLE, show_header=True, header_style="bold dim")
    table.add_column("Time",   width=10)
    table.add_column("From",   style="cyan",    width=20)
    table.add_column("To",     style="magenta", width=38)
    table.add_column("Status", width=12)
    table.add_column("MS",     style="yellow",  width=7, justify="right")

    def on_msg(msg):
        ts  = msg.get("timestamp", "")[:19].replace("T", " ")[11:]
        frm = str(msg.get("from", "?"))[:19]
        to  = str(msg.get("to",   "?"))[:37]
        ms  = str(msg.get("elapsed_ms", "—"))
        table.add_row(ts, frm, to, _status_badge(msg.get("status","?")), ms)
        console.print(table)

    tracer.start_trace(on_message=on_msg)
    try:
        while True:
            time.sleep(0.3)
    except KeyboardInterrupt:
        tracer.stop_trace()
        console.print("[green]Trace stopped.[/]")


def cmd_summary():
    s = tracer.summarize()
    failures = tracer.get_failures()
    slow     = tracer.get_slow_calls()

    stats = [
        Panel(f"[bold white]{s['total_messages']}[/]\n[dim]Total Messages[/]",  border_style="blue"),
        Panel(f"[bold green]{s['ok']}[/]\n[dim]Successful[/]",                  border_style="green"),
        Panel(f"[bold red]{s['errors']}[/]\n[dim]Errors[/]",                    border_style="red"),
        Panel(f"[bold yellow]{s['avg_response_ms']}ms[/]\n[dim]Avg Response[/]",border_style="yellow"),
        Panel(f"[bold cyan]{s['unique_endpoints']}[/]\n[dim]Endpoints[/]",       border_style="cyan"),
    ]
    console.print(Columns(stats, equal=True, expand=True))

    if failures:
        console.print(Rule("[red]Recent Failures[/]"))
        for f in failures[-5:]:
            err = str(f.get("response", {}).get("error", f.get("status","?")))[:60]
            console.print(f"  [dim]#{f.get('id')}[/] [red]{f.get('from')} → {f.get('to')}[/]: {err}")

    if slow:
        console.print(Rule("[yellow]Slow Calls (>1s)[/]"))
        for sc in slow[-5:]:
            console.print(f"  [dim]#{sc.get('id')}[/] [yellow]{sc.get('from')} → {sc.get('to')}[/]: {sc.get('elapsed_ms')}ms")


def cmd_simulate():
    url   = Prompt.ask("[cyan]Target agent URL[/]")
    count = IntPrompt.ask("Number of messages", default=5)
    payload = {"message": "ping from simulated agent", "source": "agent_postman_sim"}
    with console.status(f"[bold cyan]Flood testing {url} with {count} messages...[/]"):
        result = simulator.flood_test(url, payload, count=count, concurrency=2)
    console.print(Panel(
        f"[green]Success: {result['success']}[/]  [red]Errors: {result['errors']}[/]\n"
        f"Avg: [yellow]{result['avg_ms']}ms[/]  Min: {result['min_ms']}ms  Max: {result['max_ms']}ms",
        title="[bold]Flood Test Results[/]",
        border_style="cyan",
    ))


def cmd_inject():
    sender   = Prompt.ask("[cyan]Sender agent name[/]", default="test_agent")
    receiver = Prompt.ask("[cyan]Receiver[/]",          default="target_agent")
    raw      = Prompt.ask("[cyan]JSON payload[/]",      default="{}")
    status   = Prompt.ask("[cyan]Status[/]",            default="sent")
    try:
        payload = json.loads(raw)
    except Exception:
        console.print("[red]Invalid JSON.[/]"); return
    msg = inspector.inject_test_message(sender, receiver, payload, status)
    console.print(f"[green]✓ Injected message #{msg['id']}[/]")


def cmd_replay():
    console.print("[dim]1) From message store   2) From workflow file[/]")
    choice = Prompt.ask("Choice", default="1")
    if choice == "1":
        start = IntPrompt.ask("Start ID", default=1)
        results = replayer.replay_from_store(start_id=start)
        console.print(f"[green]Replayed {len(results)} messages.[/]")
    else:
        fpath = Prompt.ask("Workflow file path")
        results = replayer.replay_from_file(fpath)
        console.print(f"[green]Replayed {len(results)} messages.[/]")

    save = Prompt.ask("Save as workflow? Enter name (blank=skip)", default="").strip()
    if save:
        path = replayer.save_workflow(save)
        console.print(f"[green]Saved → {path}[/]")


def interactive():
    console.print(BANNER)
    print_menu()
    while True:
        try:
            cmd = Prompt.ask("\n[bold blue]agent-postman[/]").strip().lower()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Goodbye.[/]"); break

        if cmd in ("q", "quit", "exit"):
            console.print("[yellow]Goodbye.[/]"); break
        elif cmd in ("1", "inspect"):   cmd_inspect()
        elif cmd in ("2", "test"):      cmd_test()
        elif cmd in ("3", "replay"):    cmd_replay()
        elif cmd in ("4", "simulate"):  cmd_simulate()
        elif cmd in ("5", "validate"):  cmd_validate()
        elif cmd in ("6", "trace"):     cmd_trace()
        elif cmd in ("7", "summary"):   cmd_summary()
        elif cmd in ("8", "inject"):    cmd_inject()
        elif cmd in ("help", "?", ""):  print_menu()
        else:
            console.print(f"[red]Unknown: '{cmd}'. Type 'help'.[/]")


def main():
    """Entry point for pip-installed CLI: `agent-postman`"""
    if len(sys.argv) > 1:
        from agent_postman.cli_args import handle
        handle(sys.argv[1:])
    else:
        interactive()


if __name__ == "__main__":
    interactive()
