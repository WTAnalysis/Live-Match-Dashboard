import base64
import math
import plotly.graph_objects as go


def combined_probability(grid_figure,wins,colours,outlines,brand_path,simulations):
    fig=go.Figure(grid_figure)
    # Place every grid element in the left half of one exportable canvas.
    for annotation in fig.layout.annotations:
        if annotation.xref=='paper':annotation.x=.075+.365*float(annotation.x)
        if annotation.yref=='paper':annotation.y=.15+.56*float(annotation.y)
    for image in fig.layout.images:
        if image.xref=='paper':
            image.x=.075+.365*float(image.x)
            image.sizex*=.365
        if image.yref=='paper':
            image.y=.15+.56*float(image.y)
            image.sizey*=.56
    fig.update_layout(title=None,width=1400,height=570,margin=dict(l=15,r=15,t=20,b=20),
                      xaxis=dict(domain=[.075,.44]),yaxis=dict(domain=[.15,.71]),
                      xaxis2=dict(domain=[.54,.98],range=[-1.12,1.12],visible=False,fixedrange=True),
                      yaxis2=dict(domain=[.10,.86],range=[-.30,1.15],visible=False,fixedrange=True),hovermode='closest')
    for x,title in [(.25,'Scoreline Probability Grid'),(.76,'Win Probability Index')]:
        fig.add_annotation(x=x,y=.98,xref='paper',yref='paper',text=f'<b>{title}</b>',showarrow=False,
                           xanchor='center',yanchor='top',font=dict(size=22,color='#24202b'))
    angle=math.pi
    for value,colour,outline in zip(wins,[colours[0],'#929398',colours[1]],[outlines[0],'#73747a',outlines[1]]):
        end=angle-math.pi*value
        points=[(math.cos(angle+(end-angle)*i/70),math.sin(angle+(end-angle)*i/70)) for i in range(71)]
        points += [(.72*math.cos(end+(angle-end)*i/70),.72*math.sin(end+(angle-end)*i/70)) for i in range(71)]
        path='M '+' L '.join(f'{x:.6f},{y:.6f}' for x,y in points)+' Z'
        fig.add_shape(type='path',path=path,xref='x2',yref='y2',fillcolor=colour,line=dict(color=outline,width=1.5))
        angle=end
    for x,label,value in zip([-.49,0,.49],['Home Win','Draw','Away Win'],wins):
        fig.add_annotation(x=x,y=.12,xref='x2',yref='y2',text=f'<b>{label}<br>{value:.1%}</b>',showarrow=False,font=dict(size=17))
    brand='data:image/png;base64,'+base64.b64encode(brand_path.read_bytes()).decode()
    fig.add_layout_image(source=brand,xref='x2',yref='y2',x=0,y=.43,sizex=.5,sizey=.4,xanchor='center',yanchor='middle',sizing='contain')
    fig.add_annotation(x=0,y=-.19,xref='x2',yref='y2',text=f'Based on {simulations:,} simulations of individual shot events',showarrow=False,font=dict(size=12,color='#777'))
    # A trace registers the second pair of axes for rendering and export.
    fig.add_trace(go.Scatter(x=[0],y=[0],xaxis='x2',yaxis='y2',mode='markers',marker=dict(opacity=0),hoverinfo='skip',showlegend=False))
    return fig
