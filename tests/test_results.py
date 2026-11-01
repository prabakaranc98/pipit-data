from concurrent.futures import ThreadPoolExecutor

from pipit.results import Results


def test_rows_survive_a_stop_and_the_latest_row_wins(tmp_path) -> None:
    path = tmp_path / "answers.jsonl"
    first = Results(path, key="case_id")
    first.add({"case_id": "a", "choice": None, "error": "refused"})
    first.add({"case_id": "b", "choice": "hold"})
    # The run stops here; a new run reads what was saved.
    again = Results(path, key="case_id")
    assert again.get("b")["choice"] == "hold" and again.get("c") is None
    again.add({"case_id": "a", "choice": "proceed"})
    rows = Results(path, key="case_id").compact(["b", "a", "c"])
    assert [(r["case_id"], r["choice"]) for r in rows] == [("b", "hold"), ("a", "proceed")]
    assert len(path.read_text().splitlines()) == 2  # compacting leaves one row per item


def test_rows_added_from_many_threads_are_all_kept(tmp_path) -> None:
    results = Results(tmp_path / "answers.jsonl", key="row")
    with ThreadPoolExecutor(8) as pool:
        list(pool.map(lambda i: results.add({"row": i, "answer": i * 2}), range(200)))
    reread = Results(tmp_path / "answers.jsonl", key="row")
    assert all(reread.get(i)["answer"] == i * 2 for i in range(200))


def test_a_half_written_last_row_is_dropped_not_fatal(tmp_path) -> None:
    path = tmp_path / "answers.jsonl"
    path.write_text('{"case_id": "a", "choice": "hold"}\n{"case_id": "b", "cho')
    results = Results(path, key="case_id")
    assert results.get("a")["choice"] == "hold" and results.get("b") is None
    results.add({"case_id": "b", "choice": "ask"})
    assert [Results(path, key="case_id").get(k)["choice"] for k in ("a", "b")] == ["hold", "ask"]


def test_a_last_row_cut_before_its_newline_is_kept(tmp_path) -> None:
    path = tmp_path / "answers.jsonl"
    # A run stopped after writing row b but before its newline.
    path.write_text('{"case_id": "a", "choice": "hold"}\n{"case_id": "b", "choice": "ask"}')
    results = Results(path, key="case_id")
    results.add({"case_id": "c", "choice": "proceed"})
    results.add({"case_id": "d", "choice": "hold"})
    inode = path.stat().st_ino
    again = Results(path, key="case_id")  # b and c once ran together on one line, and this raised
    assert [again.get(k)["choice"] for k in "abcd"] == ["hold", "ask", "proceed", "hold"]
    assert path.stat().st_ino == inode  # a whole file is only read, never rewritten
