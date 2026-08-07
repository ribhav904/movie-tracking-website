"use client";

import { useState } from "react";
import { ArrowLeftRight, Equal, Info, Trophy } from "lucide-react";

import { PageHeader } from "@/components/page-header";
import { demoMedia } from "@/lib/demo-data";
import type { MediaType } from "@/lib/types";

const types: Array<{ value: MediaType; label: string }> = [{ value: "movie", label: "Films" }, { value: "tv", label: "Television" }, { value: "game", label: "Games" }, { value: "book", label: "Books" }];

export default function ArenaPage() {
  const [mediaType, setMediaType] = useState<MediaType>("movie");
  const [answered, setAnswered] = useState(false);
  const left = demoMedia[0];
  const right = demoMedia[4];
  return <div className="page-stack">
    <PageHeader eyebrow="Battle Arena" title="Which one stays with you?" description="A deliberate head-to-head comparison creates a Battle Score that remains separate from your manual and public ratings." />
    <section className="arena-controls"><div className="segmented-control">{types.map((type) => <button key={type.value} className={mediaType === type.value ? "is-active" : ""} onClick={() => { setMediaType(type.value); setAnswered(false); }}>{type.label}</button>)}</div><span><Info size={15} /> No repeated pairs · ties allowed</span></section>
    <section className={`arena-matchup ${answered ? "arena-matchup--answered" : ""}`}>
      <ArenaItem side="left" title={left.title} meta="2019 · Thriller" score="1,586" publicRating="8.5" onChoose={() => setAnswered(true)} />
      <div className="arena-matchup__middle"><span>or</span><button onClick={() => setAnswered(true)} className="tie-button" aria-label="Choose a tie"><Equal size={19} /></button><small>Tie</small></div>
      <ArenaItem side="right" title={right.title} meta="2010 · Mystery" score="1,524" publicRating="8.2" onChoose={() => setAnswered(true)} />
    </section>
    <section className="arena-footer panel"><div><Trophy size={18} /><p><strong>Battle Score is provisional</strong><br />It settles after five comparisons. New titles begin at Elo 1500.</p></div>{answered ? <button className="button button--primary" onClick={() => setAnswered(false)}><ArrowLeftRight size={16} /> Next pairing</button> : <p className="muted-copy">Choose a title, or mark the pair equal.</p>}</section>
  </div>;
}

function ArenaItem({ side, title, meta, score, publicRating, onChoose }: { side: "left" | "right"; title: string; meta: string; score: string; publicRating: string; onChoose: () => void }) { return <article className={`arena-item arena-item--${side}`}><div className="arena-item__cover"><span>{title.slice(0, 1)}</span></div><p className="eyebrow">{meta}</p><h2>{title}</h2><dl><div><dt>Battle score</dt><dd>{score}</dd></div><div><dt>Public rating</dt><dd>{publicRating}</dd></div></dl><button className="button button--secondary" onClick={onChoose}>This one</button></article>; }
