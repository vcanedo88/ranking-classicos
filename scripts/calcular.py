"""Calcula o Índice de Freguesia 2.0 a partir de dados/jogos.csv.

Uso:  python3 scripts/calcular.py
Saída: data/*.json (lidos pelo site) e csv/*.csv (mesmos dados em CSV).

Para atualizar o ranking depois de um novo clássico, acrescente uma linha em
dados/jogos.csv (qualquer ordem) e rode o script de novo.
"""
import csv, json, os, datetime as dt
from collections import defaultdict

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *x: os.path.join(RAIZ, *x)

PESOS = json.load(open(P("dados", "pesos.json"), encoding="utf-8"))
CLASSICOS = json.load(open(P("dados", "classicos.json"), encoding="utf-8"))
REC = PESOS["recencia"]            # blocos de 10 jogos, do mais recente ao mais antigo
W = PESOS["importancia"]
KO = {"SF", "F", "QF", "1/8", "1/16", "4F", "FP"}   # fases eliminatórias (códigos do oGol)
FILTROS = ["Todas", "Estaduais", "Brasileirão", "Copas", "Mata-mata"]
JANELAS = [50, 40, 30, 20, 10]
COMPNOME = {"BR": "Brasileirão", "SB": "Série B", "CB": "Copa do Brasil", "LIB": "Libertadores", "SUL": "Sul-Americana",
            "REC": "Recopa", "SUP": "Supercopa", "PL": "Primeira Liga", "NE": "Copa do Nordeste"}
ESTNOME = {"RJ": "Carioca", "SP": "Paulistão", "RS": "Gauchão", "MG": "Mineiro", "BA": "Baiano", "PR": "Paranaense"}
FASENOME = {"F": "Final", "SF": "Semifinal", "QF": "Quartas", "1/8": "Oitavas", "1/16": "16 avos", "4F": "4ª fase"}


def ler_jogos():
    por = defaultdict(list)
    for r in csv.DictReader(open(P("dados", "jogos.csv"), encoding="utf-8")):
        pen = (int(r["pen_mandante"]), int(r["pen_visitante"])) if r["pen_mandante"] else None
        por[r["classico"]].append(dict(data=r["data"], m=r["mandante"], v=r["visitante"], gm=int(r["gm"]), gv=int(r["gv"]),
                                      comp=r["competicao"], temp=r["temporada"], fase=r["fase"], pen=pen, tipo=r["tipo"],
                                      vantagem=r["avancou_por_vantagem"], obs=r["obs"]))
    for k in por:
        por[k].sort(key=lambda g: g["data"], reverse=True)
    return por


def grupo(g):
    return {"EST": "Estaduais", "BR": "Brasileirão", "SB": "Brasileirão"}.get(g["comp"], "Copas")


def imp(g):
    if g["tipo"] == "consolacao":
        return W["estadual"]
    c, ko = g["comp"], g["fase"] in KO
    if c in ("EST", "NE", "PL"):
        if not ko:
            return W["estadual"]
        if g["fase"] == "F" and g["tipo"] != "turno":
            return W["final_estadual"]
        return W["mata_mata_estadual"]
    if c == "BR":
        return W["brasileirao"]
    if c == "SB":
        return W["serie_b"]
    if c in ("SUP", "REC"):
        return W["supercopa"]
    if c in ("CB", "LIB", "SUL"):
        if g["fase"] == "F":
            return W["final_copa"]
        if ko:
            return W["mata_mata_copa"]
        return W["grupos_libertadores"] if c == "LIB" else W["grupos_sula"]
    raise ValueError(f"competição desconhecida: {g}")


def pts(g, team):
    my = g["gm"] if g["m"] == team else g["gv"]
    ot = g["gv"] if g["m"] == team else g["gm"]
    return 3 if my > ot else (1 if my == ot else 0)


def confrontos(games):
    """Agrupa jogos eliminatórios em confrontos (ida e volta ou jogo único) e define quem avançou."""
    ko = [g for g in sorted(games, key=lambda g: g["data"]) if g["fase"] in KO]
    ties = []
    for g in ko:
        key = (g["comp"], g["temp"], g["fase"])
        if ties:
            t = ties[-1]
            last = t["jogos"][-1]
            gap = (dt.date.fromisoformat(g["data"]) - dt.date.fromisoformat(last["data"])).days
            if t["key"] == key and len(t["jogos"]) == 1 and not t["jogos"][0]["pen"] and gap <= (14 if g["comp"] == "EST" else 35):
                t["jogos"].append(g)
                continue
        ties.append(dict(key=key, jogos=[g]))
    for t in ties:
        agg = defaultdict(int)
        for g in t["jogos"]:
            agg[g["m"]] += g["gm"]
            agg[g["v"]] += g["gv"]
        (a, ga), (b, gb) = list(agg.items())
        last = t["jogos"][-1]
        if ga != gb:
            w, como = (a if ga > gb else b), ("agregado" if len(t["jogos"]) > 1 else "jogo")
        elif last["pen"]:
            w, como = (last["m"] if last["pen"][0] > last["pen"][1] else last["v"]), "pênaltis"
        elif last["vantagem"]:
            w, como = last["vantagem"], "vantagem"
        else:
            w, como = None, "?"
        t.update(vencedor=w, como=como, fim=last["data"])
    return ties


def indice(team, gN, tN, filtro):
    num = den = 0.0
    n = v = e = d = cv = cl = 0
    for i, g in enumerate(gN):
        if filtro == "Mata-mata" and g["fase"] not in KO:
            continue
        if filtro in ("Estaduais", "Brasileirão", "Copas") and grupo(g) != filtro:
            continue
        w = REC[i // 10] * imp(g)
        p = pts(g, team)
        num += w * p; den += w * 3; n += 1
        v += p == 3; e += p == 1; d += p == 0
    for t in tN:
        g = t["jogos"][-1]
        if filtro in ("Estaduais", "Brasileirão", "Copas") and grupo(g) != filtro:
            continue
        w = REC[t["pos"] // 10] * imp(g)
        num += w * (3 if t["vencedor"] == team else 0); den += w * 3
        cv += t["vencedor"] == team; cl += t["vencedor"] != team
    return (round(100 * num / den, 1) if den else None), n, v, e, d, cv, cl


def nivel(i):
    return "Freguesia" if i >= PESOS["limiar_freguesia"] else ("Vantagem clara" if i >= PESOS["limiar_vantagem"] else "Equilíbrio")


def br(d):
    return f"{d[8:]}/{d[5:7]}/{d[:4]}"


def comp_nome(g, uf):
    c = ESTNOME[uf] if g["comp"] == "EST" else COMPNOME[g["comp"]]
    fase = FASENOME.get(g["fase"], "")
    if g["tipo"] == "turno": fase = "Final de turno"
    if g["tipo"] == "consolacao": fase = "Taça Rio (consolação)"
    return f"{c} {g['temp']}" + (f" · {fase}" if fase else "")


def main():
    por = ler_jogos()
    ranking, recortes, jogos, indices, matamatas = [], [], [], [], []
    for c in CLASSICOS:
        k, a, b, uf = c["id"], c["time_a"], c["time_b"], c["uf"]
        games = por[k]
        if len(games) < 50:
            raise SystemExit(f"{k}: só {len(games)} jogos na base")
        lab = f"{a} x {b}"
        g50 = games[:50]
        lim = g50[-1]["data"]
        ties = [t for t in confrontos(games) if t["fim"] >= lim]
        if any(t["vencedor"] is None for t in ties):
            raise SystemExit(f"{k}: mata-mata sem vencedor definido: {[t for t in ties if t['vencedor'] is None]}")
        pos = {g["data"]: i for i, g in enumerate(g50)}
        for t in ties:
            t["pos"] = pos[t["fim"]]
        ia, ib = indice(a, g50, ties, "Todas")[0], indice(b, g50, ties, "Todas")[0]
        dom, fre = (a, b) if ia >= ib else (b, a)

        # jejum vigente: quem está há mais jogos sem vencer
        def sem_vencer(team):
            for n, g in enumerate(games):
                if pts(g, team) == 3:
                    return n, g["data"]
            return len(games), ""
        (ja, da), (jb, db) = sem_vencer(a), sem_vencer(b)
        jt, jn, jd = (a, ja, da) if ja >= jb else (b, jb, db)

        for N in JANELAS:
            gN = g50[:N]
            limN = gN[-1]["data"]
            tN = [t for t in ties if t["fim"] >= limN]
            for f in FILTROS:
                ra, rb = indice(a, gN, tN, f), indice(b, gN, tN, f)
                if ra[1] == 0:
                    continue
                top, ot, r = (a, b, ra) if (ra[0] or 0) >= (rb[0] or 0) else (b, a, rb)
                indices.append(dict(classico=lab, filtro=f, janela=N, dominante=top, fregues=ot, indice=r[0], jogos=r[1],
                                    v=r[2], e=r[3], d=r[4], vagas_dom=r[5], vagas_fre=r[6], inicio=limN,
                                    poucos="S" if r[1] < max(3, round(N * 0.12)) else "N",
                                    jejum_time=jt, jejum_jogos=jn, jejum_desde=jd, inicio50=lim, nivel=nivel(r[0])))
        for n in (10, 20, 30, 40, 50):
            s = g50[:n]
            wd = sum(pts(g, dom) == 3 for g in s); e = sum(g["gm"] == g["gv"] for g in s)
            gd = sum(g["gm"] if g["m"] == dom else g["gv"] for g in s)
            gf = sum(g["gv"] if g["m"] == dom else g["gm"] for g in s)
            recortes.append(dict(classico=lab, recorte=n, dominante=dom, fregues=fre, v_dom=wd, empates=e, v_fregues=n - wd - e,
                                 gols_dom=gd, gols_fregues=gf, aproveitamento=round(100 * (3 * wd + e) / (3 * n), 1), desde=s[-1]["data"]))
        rc = recortes[-5:]
        i0 = indice(dom, g50, ties, "Todas")
        last = next((g for g in games if pts(g, fre) == 3), None)
        vd = sum(t["vencedor"] == dom for t in ties)
        u = games[0]
        ranking.append(dict(classico=lab, apelido=c["apelido"], uf=uf, time_a=a, time_b=b, dominante=dom, fregues=fre,
                            indice=i0[0], indice_simples=round(sum(r["aproveitamento"] for r in rc) / 5, 1),
                            ap10=rc[0]["aproveitamento"], ap20=rc[1]["aproveitamento"], ap30=rc[2]["aproveitamento"],
                            ap40=rc[3]["aproveitamento"], ap50=rc[4]["aproveitamento"],
                            campanha50=f"{i0[2]}V {i0[3]}E {i0[4]}D", mata_matas=f"{vd} x {len(ties) - vd}",
                            jejum=next((n for n, g in enumerate(games) if pts(g, fre) == 3), len(games)),
                            ult_vit_fregues=(f"{br(last['data'])} {last['m']} {last['gm']}x{last['gv']} {last['v']}" if last else ""),
                            ultimo_jogo=f"{br(u['data'])} {u['m']} {u['gm']}x{u['gv']} {u['v']}"))
        for i, g in enumerate(g50, 1):
            t = next((t for t in ties if t["fim"] == g["data"]), None)
            jogos.append(dict(classico=lab, n=i, data=g["data"], mandante=g["m"], gm=g["gm"], gv=g["gv"], visitante=g["v"],
                              competicao=comp_nome(g, uf), categoria=grupo(g), mata_mata="S" if g["fase"] in KO else "N",
                              penaltis=f"{g['pen'][0]}-{g['pen'][1]}" if g["pen"] else "",
                              vencedor=g["m"] if g["gm"] > g["gv"] else (g["v"] if g["gv"] > g["gm"] else "Empate"),
                              classificado=t["vencedor"] if t else "", como=t["como"] if t else "",
                              peso=round(REC[(i - 1) // 10] * imp(g), 2), obs=g["obs"]))
        for t in sorted(ties, key=lambda t: t["fim"], reverse=True):
            g = t["jogos"][-1]
            placares = " / ".join(f"{x['m']} {x['gm']}x{x['gv']} {x['v']}" + (f" (pên. {x['pen'][0]}-{x['pen'][1]})" if x["pen"] else "") for x in t["jogos"])
            nome = comp_nome(g, uf)
            matamatas.append(dict(classico=lab, data=g["data"], competicao=nome.split(" · ")[0],
                                  fase=nome.split(" · ")[1] if " · " in nome else g["fase"], jogos=placares,
                                  avancou=t["vencedor"], como=t["como"], peso=round(REC[t["pos"] // 10] * imp(g), 2)))

    ranking.sort(key=lambda r: -r["indice"])
    for p, r in enumerate(ranking, 1):
        r["pos"] = p; r["nivel"] = nivel(r["indice"])
    for f in FILTROS:
        for N in JANELAS:
            rs = [r for r in indices if r["filtro"] == f and r["janela"] == N]
            rs.sort(key=lambda r: (r["poucos"] == "S", -(r["indice"] or 0)))
            for p, r in enumerate(rs, 1):
                r["pos"] = p
    indices.sort(key=lambda r: (FILTROS.index(r["filtro"]), -r["janela"], r["pos"]))
    pesos = [dict(grupo="Recência", criterio=f"Jogos {i * 10 + 1} a {i * 10 + 10}" + (" (mais recentes)" if i == 0 else ""), peso=REC[i]) for i in range(5)]
    pesos += [dict(grupo="Importância", criterio=PESOS["rotulos"][k], peso=W[k]) for k in PESOS["rotulos"]]
    pesos += [dict(grupo="Bônus", criterio="Classificação ou título em mata-mata: jogo extra com o peso da fase", peso="")]
    meta = dict(atualizado=dt.date.today().isoformat(), ultimo_jogo=max(g["data"] for v in por.values() for g in v))

    os.makedirs(P("data"), exist_ok=True); os.makedirs(P("csv"), exist_ok=True)
    for nome, rows in (("ranking", ranking), ("recortes", recortes), ("jogos", jogos), ("indices", indices),
                       ("matamatas", matamatas), ("pesos", pesos)):
        json.dump(rows, open(P("data", f"{nome}.json"), "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
        cols = (["pos"] + [c for c in rows[0] if c != "pos"]) if nome == "ranking" else list(rows[0].keys())
        with open(P("csv", f"{nome}.csv"), "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
    json.dump(meta, open(P("data", "meta.json"), "w", encoding="utf-8"), ensure_ascii=False)
    for r in ranking[:5]:
        print(f"{r['pos']}. {r['classico']}: {r['dominante']} {r['indice']} (jejum {r['jejum']})")


if __name__ == "__main__":
    main()
