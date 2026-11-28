"""QA-only exact terminal punctuation restoration for reconciled outcomes.

A deterministic explicit source item independently confirms the whole row.
Only an omitted final period may be restored, not a changed word or a date.
Keep original extracted metadata and description, and record the affected IDs.
"""
def restore_structured_periods(items,explicit,blocks):
    rows={r['id']:r for b in blocks for r in b}
    repaired=[];diagnostics=[]
    for index,item in enumerate(items):
        replacement=item
        if item['category'] in ('decision','action') and len(item['sources'])==1:
            ref=item['sources'][0];row=rows.get(ref['source_id'])
            if row and ref['timestamp']==row['timestamp'] and row['text']==ref['quote']+'.':
                matches=[other for other in explicit
                    if other['category']==item['category'] and other['owner']==item['owner']
                    and other['due']==item['due'] and len(other['sources'])==1
                    and other['sources'][0]=={**ref,'quote':row['text']}]
                if len(matches)==1:
                    replacement={**item,'sources':[{**ref,'quote':row['text']}]}
                    diagnostics.append({'item_index':index,'source_id':ref['source_id'],
                                        'code':'restored_exact_terminal_period'})
        repaired.append(replacement)
    return repaired,diagnostics
