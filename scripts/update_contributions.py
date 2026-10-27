"""Atualiza a grade de contribuições do GitHub em index.html e en/index.html.

Roda na GitHub Action diária (.github/workflows/contributions.yml).
Substitui o bloco entre <!-- contributions:start --> e <!-- contributions:end -->.
"""
import json, os, re, urllib.request
from datetime import date

USER = "mluizaa00"
ACCENT, ACCENT_SOFT = "#FF5C5C", "#FFE5E3"
LEVELS = {"NONE": "#ECE3D2", "FIRST_QUARTILE": "#FFC4BE", "SECOND_QUARTILE": "#FF8E86",
          "THIRD_QUARTILE": ACCENT, "FOURTH_QUARTILE": "#C9302F"}
MONTHS = {"pt": "jan fev mar abr mai jun jul ago set out nov dez".split(),
          "en": "jan feb mar apr may jun jul aug sep oct nov dec".split()}
PAGES = {"pt": "index.html", "en": "en/index.html"}


def fetch_calendar():
    query = ('query{ user(login:"%s"){ contributionsCollection{ contributionCalendar{ '
             'totalContributions weeks{ contributionDays{ date contributionCount contributionLevel } } } } } }' % USER)
    req = urllib.request.Request(
        "https://api.github.com/graphql", data=json.dumps({"query": query}).encode(), method="POST",
        headers={"Authorization": "Bearer " + os.environ["GITHUB_TOKEN"], "Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        data = json.load(r)
    return data["data"]["user"]["contributionsCollection"]["contributionCalendar"]


def caption(lang, today):
    if lang == "pt":
        return f"atualizado em {today.day} de {MONTHS['pt'][today.month - 1]}. de {today.year}"
    return f"updated {MONTHS['en'][today.month - 1].capitalize()} {today.day}, {today.year}"


def grid(cal, lang, today):
    weeks = cal["weeks"]
    labels, last = [], None
    for w in weeks:
        m = int(w["contributionDays"][0]["date"][5:7])
        labels.append(MONTHS[lang][m - 1] if m != last else "")
        last = m
    labels[0] = ""
    lab = "".join(f'<span style="font-family: \'JetBrains Mono\', monospace; font-size: 11px; white-space: nowrap; overflow: visible">{l}</span>' for l in labels)
    cells = []
    for w in weeks:
        for d in w["contributionDays"]:
            t = (f"{d['contributionCount']} contribuições em {d['date']}" if lang == "pt"
                 else f"{d['contributionCount']} contributions on {d['date']}")
            cells.append(f'<span title="{t}" style="background: {LEVELS[d["contributionLevel"]]}; border-radius: 3px"></span>')
    total = cal["totalContributions"]
    tot = f"{total:,}".replace(",", ".") if lang == "pt" else f"{total:,}"
    title = f"{tot} contribuições nos últimos 12 meses" if lang == "pt" else f"{tot} contributions in the last 12 months"
    less, more = ("menos", "mais") if lang == "pt" else ("less", "more")
    legend = "".join(f'<span style="width: 12px; height: 12px; border-radius: 3px; background: {c}"></span>' for c in LEVELS.values())
    summary = f"Gráfico de contribuições no GitHub: {title}." if lang == "pt" else f"GitHub contributions chart: {title}."
    dot = 'width: 11px; height: 11px; border-radius: 999px; border: 2px solid #16120F; background: '
    return f'''<div class="card" style="background: #FFFFFF; border: 2.5px solid #16120F; border-radius: 22px; box-shadow: 8px 8px 0 #16120F; overflow: hidden">
<div aria-hidden="true" style="display: flex; align-items: center; gap: 12px; padding: 10px 16px; border-bottom: 2.5px solid #16120F">
<span style="display: flex; gap: 6px"><span style="{dot}{ACCENT}"></span><span style="{dot}{ACCENT_SOFT}"></span><span style="{dot}#FFFFFF"></span></span>
<span style="font-family: 'JetBrains Mono', monospace; font-size: 12px; font-weight: 600">git log --since="1 year ago"</span>
</div>
<div style="padding: 24px; display: flex; flex-direction: column; gap: 18px">
<div style="display: flex; flex-wrap: wrap; justify-content: space-between; align-items: baseline; gap: 12px">
<h3 style="margin: 0; font-family: 'Bricolage Grotesque', sans-serif; font-weight: 800; font-size: 28px; line-height: 1.05">{title}</h3>
<a href="https://github.com/{USER}" style="font-family: 'JetBrains Mono', monospace; font-size: 13px; font-weight: 600">github.com/{USER} →</a>
</div>
<div role="img" aria-label="{summary}" style="overflow-x: auto; padding-bottom: 4px">
<div style="display: grid; grid-template-columns: repeat({len(weeks)}, 13px); gap: 3px; width: max-content">{lab}</div>
<div style="display: grid; grid-auto-flow: column; grid-template-rows: repeat(7, 13px); grid-auto-columns: 13px; gap: 3px; width: max-content; margin-top: 6px">{"".join(cells)}</div>
</div>
<div style="display: flex; flex-wrap: wrap; justify-content: space-between; gap: 12px; font-family: 'JetBrains Mono', monospace; font-size: 12px">
<span>{caption(lang, today)}</span>
<span aria-hidden="true" style="display: flex; align-items: center; gap: 4px">{less} {legend} {more}</span>
</div>
</div>
</div>
'''


def main():
    cal, today = fetch_calendar(), date.today()
    pattern = re.compile(r"<!-- contributions:start -->\n.*?<!-- contributions:end -->", re.S)
    for lang, path in PAGES.items():
        html = open(path, encoding="utf-8").read()
        new = pattern.sub(lambda _: "<!-- contributions:start -->\n" + grid(cal, lang, today) + "<!-- contributions:end -->", html, count=1)
        if new == html and not pattern.search(html):
            raise SystemExit(f"marcadores não encontrados em {path}")
        open(path, "w", encoding="utf-8").write(new)
    print("total:", cal["totalContributions"])


if __name__ == "__main__":
    main()
