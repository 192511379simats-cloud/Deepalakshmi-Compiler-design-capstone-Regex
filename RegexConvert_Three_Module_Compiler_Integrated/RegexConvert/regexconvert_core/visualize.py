from html import escape
import math
def automaton_svg(a, width=760, height=420):
    states=a["states"]; n=len(states)
    if n==0: return ""
    # Circular layout with extra room for labels and accepting circles.
    cx,cy=width/2,height/2
    # Keep every state and its accepting ring comfortably inside the viewBox.
    # The earlier radius scaled too aggressively for larger NFAs and clipped
    # states at the top/bottom of the visible diagram.
    radius=min(width*0.28, height*0.25, max(48, n*12))
    pos={}
    for i,s in enumerate(states):
        angle=-math.pi/2+2*math.pi*i/n
        pos[s]=(cx+radius*math.cos(angle),cy+radius*math.sin(angle))
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" preserveAspectRatio="xMidYMid meet" aria-label="{escape(a["kind"])} state diagram">']
    parts.append('<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto"><path d="M0,0 L0,6 L7,3 z" fill="#527C78"/></marker></defs>')
    sx,sy=pos[a["start"]]
    parts.append(f'<path d="M {max(12,sx-68)} {sy} L {sx-31} {sy}" stroke="#527C78" stroke-width="2" fill="none" marker-end="url(#arrow)"/>')
    # Group edges by src/dst; self loops separately
    edges=[]
    for src,row in a["transitions"].items():
        for sym,dest in row.items():
            dests=dest if isinstance(dest,list) else [dest]
            for dst in dests: edges.append((src,str(sym),dst))
    for src,sym,dst in edges:
        x1,y1=pos[src]; x2,y2=pos[dst]
        if src==dst:
            parts.append(f'<path d="M {x1-12} {y1-18} C {x1-42} {y1-65}, {x1+42} {y1-65}, {x1+12} {y1-18}" stroke="#527C78" stroke-width="1.7" fill="none" marker-end="url(#arrow)"/>')
            parts.append(f'<text x="{x1}" y="{y1-54}" text-anchor="middle" font-size="12" fill="#26364A">{escape(sym)}</text>')
        else:
            dx,dy=x2-x1,y2-y1; dist=max(1,math.hypot(dx,dy)); ux,uy=dx/dist,dy/dist
            ax,ay=x1+ux*23,y1+uy*23; bx,by=x2-ux*26,y2-uy*26
            # Slight curvature avoids some overlap on reciprocal edges.
            mx,my=(ax+bx)/2,(ay+by)/2
            parts.append(f'<path d="M {ax:.1f} {ay:.1f} Q {mx:.1f} {my-13:.1f} {bx:.1f} {by:.1f}" stroke="#527C78" stroke-width="1.7" fill="none" marker-end="url(#arrow)"/>')
            parts.append(f'<text x="{mx:.1f}" y="{my-12:.1f}" text-anchor="middle" font-size="12" fill="#26364A">{escape(sym)}</text>')
    accepting=set(a["accepting"])
    for s,(x,y) in pos.items():
        fill="#E4ECE9" if s in accepting else "#FFFFFF"
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="22" fill="{fill}" stroke="#14243A" stroke-width="1.8"/>')
        if s in accepting: parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="17" fill="none" stroke="#14243A" stroke-width="1.2"/>')
        parts.append(f'<text x="{x:.1f}" y="{y+4:.1f}" text-anchor="middle" font-size="12" font-family="monospace" fill="#14243A">{escape(s[:8])}</text>')
    parts.append("</svg>")
    return "".join(parts)
