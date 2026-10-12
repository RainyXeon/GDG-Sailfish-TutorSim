const mmss = (s) => `${Math.floor(s / 60)} phút ${s % 60} giây`;

export default function ExamResult({ result, onHome }) {
  const wrong = result.results.filter((r) => !r.is_correct);
  const mis = [...new Map(wrong.filter((r) => r.misconception_id).map((r) => [r.misconception_id, r.misconception_name])).entries()];

  return (
    <section className="report">
      <div className="report-head">
        <div className="grade" aria-label={`Điểm ${result.score10} trên 10`}>
          <span className="grade-num">{result.score10.toFixed(1)}</span><span className="grade-of">/10</span>
        </div>
        <div>
          <h1 className="title">{result.exam_title}</h1>
          <p className="lead">Đúng {result.correct}/{result.total} câu trong {mmss(result.time_spent_sec)}.</p>
        </div>
      </div>

      {mis.length > 0 && (
        <>
          <h2 className="h2">Lỗi bạn đã mắc trong bài này</h2>
          <ul className="mis-list">
            {mis.map(([id, name]) => <li key={id}><span>{name}</span></li>)}
          </ul>
        </>
      )}

      <h2 className="h2">Xem lại từng câu</h2>
      <ul className="review">
        {result.results.map((r, i) => (
          <li key={r.question_id} className={r.is_correct ? "ok" : "bad"}>
            <p className="rv-head">
              <span>Câu {i + 1}</span>
              <span>{r.is_correct ? "Đúng" : r.chosen ? `Bạn chọn ${r.chosen}, đáp án ${r.correct_answer}` : `Bỏ trống, đáp án ${r.correct_answer}`}</span>
            </p>
            {!r.is_correct && <p className="rv-exp">{r.explanation}</p>}
          </li>
        ))}
      </ul>
      <div className="row" style={{ marginTop: 24 }}>
        <button className="btn primary" onClick={onHome}>Về trang của tôi</button>
      </div>
    </section>
  );
}
