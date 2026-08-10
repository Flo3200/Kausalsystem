from kausalrechner.graph import KausalGraph, Kausalkante, berechne_kausalkette


def test_einfache_kette():
    kanten = [Kausalkante("a", "b", "effekt * 0.5")]
    graph = KausalGraph(kanten)
    schritte, aggregiert = berechne_kausalkette(graph, "a", 10, {})
    assert len(schritte) == 1
    assert schritte[0].ausgehender_effekt == 5
    assert aggregiert == {"b": 5}


def test_zyklus_terminiert():
    kanten = [Kausalkante("a", "b", "effekt"), Kausalkante("b", "a", "effekt")]
    graph = KausalGraph(kanten)
    schritte, aggregiert = berechne_kausalkette(graph, "a", 10, {}, max_tiefe=50)
    # a -> b wird durchlaufen, b -> a wird als Zyklus abgefangen
    assert len(schritte) == 1
    assert schritte[0].von == "a" and schritte[0].nach == "b"


def test_max_tiefe_greift():
    kanten = [Kausalkante("a", "b", "effekt"), Kausalkante("b", "c", "effekt"), Kausalkante("c", "d", "effekt")]
    graph = KausalGraph(kanten)
    schritte, _ = berechne_kausalkette(graph, "a", 10, {}, max_tiefe=2)
    assert len(schritte) == 2


def test_formel_mit_parametern_und_tiefe():
    kanten = [Kausalkante("a", "b", "effekt * elastizitaet / (1 + tiefe)")]
    graph = KausalGraph(kanten)
    schritte, _ = berechne_kausalkette(graph, "a", 10, {"elastizitaet": 0.5})
    assert schritte[0].ausgehender_effekt == 5  # tiefe=0 -> /1
