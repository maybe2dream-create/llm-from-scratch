from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import HexColor
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image
pdfmetrics.registerFont(TTFont('Korean','/System/Library/Fonts/Supplemental/Arial Unicode.ttf'))
# 저장소 루트에서 실행하는 것을 전제로 한 상대경로. 두 폴더 모두 빌드 산출물이라
# 저장소에 없을 수 있으므로 먼저 만든다.
import os
EQ_DIR='tmp/pdfs'
os.makedirs(EQ_DIR,exist_ok=True); os.makedirs('output/pdf',exist_ok=True)
OUT='output/pdf/attention_mechanisms_ko.pdf'
c=canvas.Canvas(OUT,pagesize=(595.28,841.89))
c.setTitle('Attention 메커니즘: Self, Causal, Multi-head')
c.setAuthor('Codex')
y=0; eqn=0

def text(s,size=11,color='#263449',gap=21):
 global y
 c.setFillColor(HexColor(color)); c.setFont('Korean',size)
 c.drawString(48,y,s); y-=gap

def para(lines):
 for s in lines: text(s)
 ygap(8)
def ygap(n):
 global y
 y-=n

def equation(s,h=48):
 global y,eqn
 eqn+=1
 fig=plt.figure(figsize=(9,1)); fig.text(.5,.5,'$'+s+'$',ha='center',va='center',fontsize=17)
 p=f'{EQ_DIR}/eq{eqn}.png'; fig.savefig(p,dpi=220,bbox_inches='tight',pad_inches=.13,transparent=True); plt.close(fig)
 im=Image.open(p); w,hh=im.size; width=min(475,w*0.32); height=width*hh/w
 c.drawImage(p,48+(499-width)/2,y-height,width=width,height=height,mask='auto'); y-=max(h,height+15)

def page(n,title,sub):
 global y
 c.setFillColor(HexColor('#176B83')); c.rect(0,824,595,18,fill=1,stroke=0)
 y=787;text('ATTENTION / 수식으로 이해하기',10,'#176B83',30)
 text(title,23,'#112B40',36);text(sub,10,'#607082',30)
 c.setFont('Korean',9);c.setFillColor(HexColor('#607082'));c.drawString(48,32,'LLM 기초 • 행 벡터 기준 • softmax는 각 행에 적용');c.drawRightString(547,32,str(n))
def end(): c.showPage()

page(1,'1. Self-attention','각 토큰이 같은 시퀀스의 토큰들을 참고해 문맥 표현을 만듭니다.')
para(['입력 X의 i번째 행 xᵢ는 i번째 토큰의 표현입니다. 토큰 수는 n,', '모델 차원은 d_model입니다. 위치 정보는 보통 입력에 더하거나 별도로 반영합니다.'])
equation(r'X\in\mathbb{R}^{n\times d_{model}}')
text('Query, Key, Value: 세 가지 학습 가능한 투영',14,'#176B83',27)
equation(r'Q=XW_Q,\quad K=XW_K,\quad V=XW_V')
para(['W_Q, W_K의 크기: d_model × d_k; W_V의 크기: d_model × d_v.', '따라서 Q, K는 n × d_k이고, V는 n × d_v입니다.', 'Query는 찾고 싶은 정보, Key는 비교 기준, Value는 합칠 정보입니다.'])
equation(r'S=\frac{QK^{\mathsf{T}}}{\sqrt{d_k}},\quad A=\operatorname{softmax}_{row}(S),\quad Z=AV')
para(['S와 A의 크기는 n × n, 출력 Z의 크기는 n × d_v입니다.', 'A의 i번째 행은 i번째 토큰이 각 토큰을 참고하는 비율입니다.'])
equation(r'a_{ij}=\frac{\exp(q_i k_j^{\mathsf{T}}/\sqrt{d_k})}{\sum_{\ell=1}^{n}\exp(q_i k_\ell^{\mathsf{T}}/\sqrt{d_k})},\quad z_i=\sum_{j=1}^{n}a_{ij}v_j')
para(['각 가중치는 0 이상이고 행의 합은 1입니다. 출력은 Value의 가중합입니다.', '√d_k로 나누면 내적의 크기가 차원에 따라 커지는 것을 완화하여', 'softmax가 지나치게 뾰족해지는 것을 줄입니다. 성분이 독립이고 분산이', '약 1이면 내적의 분산은 약 d_k라는 가정이 이 스케일링의 근거입니다.'])
end()
page(2,'2. Causal attention','미래 토큰을 가려서, 현재 위치까지의 정보만 사용합니다.')
para(['일반적인 마스크 없는 self-attention은 모든 위치를 참고할 수 있습니다.', '다음 토큰을 예측하는 언어 모델에서는 학습 중 미래 정답을 보지 않도록', 'causal mask를 적용합니다. i번째 위치는 j ≤ i인 위치만 참고합니다.'])
equation(r'M_{ij}=0\ (j\leq i),\qquad M_{ij}=-\infty\ (j>i)')
equation(r'A=\operatorname{softmax}_{row}\left(\frac{QK^{\mathsf{T}}}{\sqrt{d_k}}+M\right),\quad Z=AV')
para(['마스크는 softmax 전에 점수에 더합니다. exp(-∞) = 0이므로 미래 위치의', '가중치는 0이 되고, 허용된 위치들의 가중치만 합이 1이 되도록 정규화됩니다.'])
para(['4개 토큰의 마스크: 아래 삼각형과 대각선은 0, 나머지는 -∞.', '행 1: [0, -∞, -∞, -∞]    행 2: [0, 0, -∞, -∞]', '행 3: [0, 0, 0, -∞]       행 4: [0, 0, 0, 0]'])
text('가중치 예: 세 번째 토큰은 어디를 볼 수 있을까요?',14,'#176B83',28)
para(['마스크 적용 전 세 번째 행의 점수가 [1, 2, 0, 3]이라고 가정합니다.', '네 번째 위치는 미래이므로 점수 3이 -∞로 바뀝니다.'])
equation(r'\operatorname{softmax}([1,2,0,-\infty])\approx[0.245,0.665,0.090,0]')
equation(r'z_3\approx0.245v_1+0.665v_2+0.090v_3')
para(['자기 자신의 위치도 허용합니다. 위치 i의 출력으로 다음 토큰 xᵢ₊₁을', '예측하므로 학습 입력과 목표를 한 칸 이동해 맞춥니다.', 'Causal self-attention은 self-attention에 시간 방향의 제한을 더한 형태입니다.'])
end()
page(3,'3. Multi-head attention','여러 투영 공간에서 attention을 계산하고 그 결과를 결합합니다.')
para(['하나의 attention 대신 h개의 head를 사용합니다. 각 head는 서로 다른', 'W_Q, W_K, W_V를 학습하여 입력의 다른 관계를 표현할 수 있습니다.', '아래에서 r은 head 번호이고, 각 head의 입력 X는 같습니다.'])
equation(r'Q_r=XW_Q^{(r)},\quad K_r=XW_K^{(r)},\quad V_r=XW_V^{(r)}')
equation(r'H_r=\operatorname{softmax}_{row}\left(\frac{Q_rK_r^{\mathsf{T}}}{\sqrt{d_k}}+M\right)V_r')
para(['마스크 없는 self-attention이면 M은 영행렬입니다.', 'Causal multi-head self-attention이면 각 head에 causal mask를 적용합니다.'])
equation(r'\operatorname{MHA}(X)=\operatorname{Concat}(H_1,\ldots,H_h)W_O')
para(['각 H_r의 크기는 n × d_v이며, 연결한 행렬은 n × (h d_v)입니다.', '출력 투영 W_O의 크기는 (h d_v) × d_model이므로 최종 출력은', 'n × d_model입니다. Head의 결과는 평균내지 않고 연결한 뒤 투영합니다.'])
text('차원 예시',14,'#176B83',28)
equation(r'd_{model}=512,\quad h=8,\quad d_k=d_v=64')
para(['각 head: n × 64 → 8개 연결: n × 512 → 출력 투영: n × 512.', 'd_k = d_v = d_model / h는 흔한 설정이며 반드시 필요한 조건은 아닙니다.'])
text('왜 여러 head를 사용할까요?',14,'#176B83',28)
para(['각 head는 서로 다른 유사도와 Value 표현을 학습할 수 있습니다.', '예를 들어 근접 토큰 관계나 먼 위치의 관련 정보를 다르게 반영할 수 있지만,', '특정 head의 역할이 문법·의미 등으로 고정되거나 보장되는 것은 아닙니다.', 'W_O는 여러 head가 얻은 정보를 다시 섞어 다음 층에 전달합니다.'])
end()
page(4,'4. 세 개념의 관계와 계산 흐름','Self / causal / multi-head는 서로 다른 관점의 개념입니다.')
text('Self-attention: 정보의 출처',14,'#176B83',28)
para(['Q, K, V가 같은 입력 시퀀스에서 만들어집니다.', 'Cross-attention에서는 Q의 입력과 K, V의 입력이 서로 다를 수 있습니다.'])
text('Causal attention: 볼 수 있는 위치',14,'#176B83',28)
para(['미래 위치를 마스크로 차단합니다. 자기회귀 생성에 필요한 제약입니다.', '마스크 없는 self-attention은 앞뒤 문맥을 함께 참고할 수 있습니다.'])
text('Multi-head attention: 병렬 표현 방식',14,'#176B83',28)
para(['서로 다른 투영으로 여러 attention을 수행한 뒤 연결하고 투영합니다.', 'Self-attention과 cross-attention 모두 multi-head로 구성할 수 있습니다.'])
equation(r'X\ \longrightarrow\ (Q_r,K_r,V_r)\ \longrightarrow\ S_r+M\ \longrightarrow\ A_r\ \longrightarrow\ H_r')
equation(r'(H_1,\ldots,H_h)\ \longrightarrow\ \operatorname{Concat}\ \longrightarrow\ W_O\ \longrightarrow\ Z')
text('Transformer에서의 위치',14,'#176B83',28)
para(['실제 Transformer block은 attention 외에 residual connection,', 'normalization, feed-forward network 등을 포함합니다.', '여기서 정의한 Z는 attention 부분의 출력이며 block 전체 출력은 아닙니다.'])
text('계산량을 이해하는 핵심',14,'#176B83',28)
para(['표준 구현은 각 head에서 n × n 점수 행렬을 계산합니다.', 'QKᵀ와 AV의 연산량은 합쳐서 O(h n² (d_k + d_v))입니다.', 'd_k = d_v = d_model / h라면 O(n² d_model)입니다.', '이는 attention 행렬 곱의 비용이며, Q/K/V 및 출력 투영 비용은 별도입니다.', 'Causal mask는 의존 범위를 제한하지만 일반적인 밀집 구현에서', 'n² 점수 행렬을 만드는 비용 자체를 없애지는 않습니다.'])
end(); c.save()
print(OUT)
