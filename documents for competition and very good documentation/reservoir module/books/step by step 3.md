```latex
\documentclass[10pt,a4paper]{article}

% ==================================================================
% PACKAGES
% ==================================================================
\usepackage[T1]{fontenc}
\usepackage[utf8]{inputenc}
\usepackage{lmodern}
\usepackage[margin=1.8cm]{geometry}
\usepackage{amsmath,amssymb,amsthm}
\usepackage{mathtools}
\usepackage{bm}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{array}
\usepackage{enumitem}
\usepackage{xcolor}
\usepackage{listings}
\usepackage{titlesec}
\usepackage{fancyhdr}
\usepackage{caption}
\usepackage{hyperref}
\usepackage{tikz}
\usepackage{siunitx}
\usepackage{multicol}
\usepackage{tabularx}
\usepackage{makecell}
\usepackage{mdframed}
\usepackage{fontawesome5}
\usetikzlibrary{arrows.meta,positioning,shapes.geometric,fit,backgrounds,calc}

\hypersetup{
  colorlinks=true,
  linkcolor=blue!50!black,
  urlcolor=blue!50!black,
  citecolor=blue!50!black,
  pdftitle={PetroLumen Reservoir Module -- AI-Operable Build Specification},
  pdfauthor={PetroLumen Engineering},
  bookmarksnumbered=true
}

\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\small\textsc{PetroLumen} --- Reservoir Module}
\fancyhead[R]{\small AI-Operable Build Specification}
\fancyfoot[L]{\small v2.0 \textperiodcentered\ \today}
\fancyfoot[R]{\thepage}
\renewcommand{\headrulewidth}{0.4pt}
\renewcommand{\footrulewidth}{0.2pt}

% ==================================================================
% COLORS
% ==================================================================
\definecolor{codebg}{RGB}{247,247,250}
\definecolor{codekw}{RGB}{0,90,160}
\definecolor{codestr}{RGB}{140,60,20}
\definecolor{codecom}{RGB}{90,120,90}
\definecolor{checkpointbg}{RGB}{255,248,220}
\definecolor{checkpointborder}{RGB}{200,150,0}
\definecolor{gatebg}{RGB}{230,245,230}
\definecolor{gateborder}{RGB}{60,140,60}
\definecolor{failbg}{RGB}{255,235,235}
\definecolor{failborder}{RGB}{180,60,60}
\definecolor{promptbg}{RGB}{235,240,255}
\definecolor{promptborder}{RGB}{60,90,180}

% ==================================================================
% LISTINGS
% ==================================================================
\lstdefinestyle{py}{
  language=Python,
  backgroundcolor=\color{codebg},
  basicstyle=\ttfamily\footnotesize,
  keywordstyle=\color{codekw}\bfseries,
  stringstyle=\color{codestr},
  commentstyle=\color{codecom}\itshape,
  numbers=left, numberstyle=\tiny\color{gray}, numbersep=6pt,
  frame=single, rulecolor=\color{gray!40},
  breaklines=true, breakatwhitespace=false,
  showstringspaces=false, tabsize=4, captionpos=b
}
\lstdefinestyle{sh}{
  language=bash,
  backgroundcolor=\color{codebg},
  basicstyle=\ttfamily\footnotesize,
  keywordstyle=\color{codekw}\bfseries,
  commentstyle=\color{codecom}\itshape,
  numbers=left, numberstyle=\tiny\color{gray}, numbersep=6pt,
  frame=single, rulecolor=\color{gray!40},
  breaklines=true, showstringspaces=false, captionpos=b
}
\lstdefinestyle{jl}{
  language=Julia,
  backgroundcolor=\color{codebg},
  basicstyle=\ttfamily\footnotesize,
  keywordstyle=\color{codekw}\bfseries,
  stringstyle=\color{codestr},
  commentstyle=\color{codecom}\itshape,
  numbers=left, numberstyle=\tiny\color{gray}, numbersep=6pt,
  frame=single, rulecolor=\color{gray!40},
  breaklines=true, showstringspaces=false, captionpos=b
}
\lstdefinestyle{matlab}{
  language=Matlab,
  backgroundcolor=\color{codebg},
  basicstyle=\ttfamily\footnotesize,
  keywordstyle=\color{codekw}\bfseries,
  commentstyle=\color{codecom}\itshape,
  numbers=left, numberstyle=\tiny\color{gray}, numbersep=6pt,
  frame=single, rulecolor=\color{gray!40},
  breaklines=true, showstringspaces=false, captionpos=b
}
\lstdefinestyle{txt}{
  backgroundcolor=\color{codebg},
  basicstyle=\ttfamily\footnotesize,
  frame=single, rulecolor=\color{gray!40},
  breaklines=true, showstringspaces=false, captionpos=b, columns=fullflexible
}
\lstset{style=py}

% ==================================================================
% CUSTOM ENVIRONMENTS
% ==================================================================
\newmdenv[
  backgroundcolor=checkpointbg,
  linecolor=checkpointborder,
  linewidth=1.5pt,
  leftline=true, rightline=true, topline=true, bottomline=true,
  innertopmargin=6pt, innerbottommargin=6pt,
  innerleftmargin=8pt, innerrightmargin=8pt,
  skipabove=8pt, skipbelow=8pt
]{aicheckpoint}

\newmdenv[
  backgroundcolor=gatebg,
  linecolor=gateborder,
  linewidth=1.5pt,
  leftline=true, rightline=true, topline=true, bottomline=true,
  innertopmargin=6pt, innerbottommargin=6pt,
  innerleftmargin=8pt, innerrightmargin=8pt,
  skipabove=8pt, skipbelow=8pt
]{gate}

\newmdenv[
  backgroundcolor=failbg,
  linecolor=failborder,
  linewidth=1.5pt,
  leftline=true, rightline=true, topline=true, bottomline=true,
  innertopmargin=6pt, innerbottommargin=6pt,
  innerleftmargin=8pt, innerrightmargin=8pt,
  skipabove=8pt, skipbelow=8pt
]{failure}

\newmdenv[
  backgroundcolor=promptbg,
  linecolor=promptborder,
  linewidth=1.5pt,
  leftline=true, rightline=true, topline=true, bottomline=true,
  innertopmargin=6pt, innerbottommargin=6pt,
  innerleftmargin=8pt, innerrightmargin=8pt,
  skipabove=8pt, skipbelow=8pt
]{aiprompt}

\titleformat{\section}{\Large\bfseries\color{blue!40!black}}{\thesection}{0.7em}{}
\titleformat{\subsection}{\large\bfseries\color{blue!30!black}}{\thesubsection}{0.5em}{}
\titleformat{\subsubsection}{\normalsize\bfseries\color{blue!20!black}}{\thesubsubsection}{0.4em}{}

\newcommand{\stepID}[1]{\textsf{\textbf{[#1]}}}
\newcommand{\cmd}[1]{\texttt{#1}}
\newcommand{\file}[1]{\texttt{#1}}

% ==================================================================
% TITLE
% ==================================================================
\title{
  \vspace{-1.2cm}
  \textbf{PetroLumen}\\[0.2em]
  \rule{\linewidth}{1pt}\\[0.3em]
  \Large Reservoir Module\\[0.2em]
  \large AI-Operable Build Specification\\[0.4em]
  \rule{\linewidth}{1pt}\\[0.6em]
  \normalsize
  A single, complete, machine-actionable document that contains\\[0.2em]
  \textbf{everything} required to build, validate, and operate the\\[0.2em]
  PetroLumen reservoir engineering workbench---written so that\\[0.2em]
  an AI assistant can read it, plan from it, and guide the user\\
  through every step, checkpoint, and validation gate.
}
\author{PetroLumen Engineering}
\date{Version 2.0 \textperiodcentered\ \today}

\begin{document}

\maketitle
\thispagestyle{empty}

\begin{abstract}
\noindent
This document is the \textbf{single source of truth} for building the
PetroLumen reservoir module. It is designed to be handed to an AI assistant
together with a request such as: \emph{``Read this document and guide me
through the build, phase by phase, checkpoint by checkpoint.''} Every phase
contains numbered steps with exact commands, expected outputs, validation
gates, common failures, and AI checkpoint prompts. The AI's job is to execute
the protocol in Section~\ref{sec:ai-protocol}: read the current phase, present
the next step, wait for the user to report the result, check it against the
expected output, and either advance or help diagnose. Nothing in this document
requires a paid software licence. Everything is achievable with open-source
tools, free benchmarks, and a single workstation.
\end{abstract}

\tableofcontents
\clearpage

% ==================================================================
\section{How to Use This Document}
\label{sec:howto}
% ==================================================================

\subsection{For the human engineer}

This document is a \textbf{linear build protocol}. Do not skip phases. Do not
proceed past a validation gate until it passes. Each phase produces a working
artifact; later phases depend on earlier ones. The total effort is roughly
12--20 months of part-time solo work, or 3--6 months for Phases 0--4 alone.

Read the whole document once before starting. Then open it at Phase~0 and work
forward.

\subsection{For the AI assistant}

You are being asked to act as a \textbf{build copilot}. Your responsibilities:

\begin{enumerate}[leftmargin=1.6em]
  \item Read Section~\ref{sec:ai-protocol} fully before responding.
  \item Ask the user which phase they are on. If they do not know, start at Phase~0.
  \item For the current phase, present steps in order. Do not dump the whole
        phase at once; present \textbf{one step at a time}.
  \item After each step, ask the user to run the command and paste the output.
  \item Compare the output against the \textbf{Expected output} in this document.
  \item If it matches: mark the step complete, and present the next step.
  \item If it does not match: consult the \textbf{Common failures} table for that
        step, and guide the user through diagnosis.
  \item At every \texttt{AI CHECKPOINT}, pause and confirm with the user that
        they want to proceed.
  \item At every \texttt{VALIDATION GATE}, run the gate commands together with
        the user and do not advance until all pass.
  \item Maintain a running log of which steps are complete, in a format the
        user can copy back to you in a future session.
\end{enumerate}

\subsection{The three marker types}

Throughout the document you will see three kinds of highlighted box:

\begin{aicheckpoint}
\textbf{AI CHECKPOINT} --- Pause here. Summarise what has been completed,
confirm the user is ready to proceed, and ask if they have any questions before
the next step.
\end{aicheckpoint}

\begin{gate}
\textbf{VALIDATION GATE} --- Run the listed commands. All must pass. If any
fails, do not proceed; diagnose using the common-failures table for the phase.
\end{gate}

\begin{failure}
\textbf{COMMON FAILURE} --- This is a known failure mode for this step. Use
the suggested diagnosis and fix.
\end{failure}

\subsection{Progress log format}

The AI should maintain a progress log in this exact format so that the user
can paste it back in a future session:

\begin{lstlisting}[style=txt]
PETRO LUMEN PROGRESS LOG
========================
Current phase: N
Current step:  N.M
Completed phases: [list]
Completed steps in current phase: [list]
Last successful command: <command>
Last output snippet: <first 5 lines of output>
Blockers: <none | description>
Date/time: <ISO timestamp>
\end{lstlisting}

% ==================================================================
\section{AI Operating Protocol}
\label{sec:ai-protocol}
% ==================================================================

\subsection{Your role}

You are the \textbf{build copilot} for the PetroLumen reservoir module. The
user is the \textbf{build engineer}. You do not run commands yourself; you
guide the user to run them, interpret their output, and decide the next action.

\subsection{Session opening ritual}

When a new session starts, your first message must be:

\begin{aiprompt}
\textbf{Session opening template.}

``Hello. I am your PetroLumen build copilot. Before we begin, please tell me:
\begin{enumerate}
  \item Which phase are you on? (If unsure, say `start from Phase 0'.)
  \item Do you have a progress log from a previous session? If yes, paste it.
  \item What operating system are you using? (Ubuntu 24.04, Ubuntu 26.04, WSL2, macOS, other?)
  \item Do you have a GPU available? (NVIDIA model, AMD model, or none?)
\end{enumerate}
Once you answer, I will present the first step of the appropriate phase.''
\end{aiprompt}

\subsection{Step presentation ritual}

For every step, your message must have this structure:

\begin{aiprompt}
\textbf{Step presentation template.}

``\stepID{Phase N, Step M} \textbf{<step title>}

\textbf{Purpose.} <one sentence on why this step exists>

\textbf{Run this command:}
\begin{verbatim}
<the exact command>
\end{verbatim}

\textbf{Expected output.} <what the user should see>

\textbf{If it works, paste the output and say `done'.}
\textbf{If it fails, paste the error and I will diagnose.''
\end{aiprompt}

\subsection{Output interpretation ritual}

When the user pastes output, your response must be one of:

\begin{enumerate}[leftmargin=1.4em]
  \item \textbf{Match:} ``Output matches expected. Step \stepID{N.M} is complete.
        Moving to \stepID{N.M+1}.'' Then present the next step.
  \item \textbf{Partial match:} ``Output is close but differs in <specific way>.
        This usually means <cause>. Try <fix>. Paste the new output.''
  \item \textbf{No match:} ``Output does not match. This is a known failure
        (see common-failures table for Phase N, Step M). Likely causes:
        <list>. Please run <diagnostic command> and paste the output.''
\end{enumerate}

\subsection{Escalation rule}

If three consecutive attempts at the same step fail, stop and present this to
the user:

\begin{aiprompt}
``We have tried three times on \stepID{Phase N, Step M} without success.
Before continuing, let us do a diagnostic sweep. Please paste the output of:
\begin{verbatim}
<diagnostic command set for this phase>
\end{verbatim}
I will then either suggest a workaround or recommend we skip this step and
revisit it after the phase's validation gate.''
\end{aiprompt}

\subsection{Never do these things}

\begin{failure}
\textbf{Forbidden AI behaviours:}
\begin{itemize}[leftmargin=1.2em]
  \item Do not present more than one step at a time, unless the user explicitly
        asks for the whole phase.
  \item Do not skip validation gates.
  \item Do not invent commands not in this document; if a fix is needed, say
        so explicitly and label it ``outside the spec''.
  \item Do not assume the user has installed something; check the phase's
        entry criteria first.
  \item Do not advance on partial output; ask for the full output.
  \item Do not paraphrase commands; reproduce them exactly.
\end{itemize}
\end{failure}

% ==================================================================
\section{Master Progress Checklist}
\label{sec:checklist}
% ==================================================================

Print or copy this checklist. Tick each gate as it passes.

\begin{longtable}{@{}p{1.2cm}p{6.8cm}p{2.4cm}p{3.2cm}@{}}
\toprule
\textbf{Gate} & \textbf{Name} & \textbf{Phase} & \textbf{Status}\\
\midrule
\endhead
G0 & Environment ready & Phase 0 & $\square$\\
G1 & Engines run SPE1 & Phase 1 & $\square$\\
G2 & Libraries tested & Phase 2 & $\square$\\
G3 & API creates and runs a case & Phase 3 & $\square$\\
G4 & SPE1/SPE9/SPE10/Norne pass & Phase 4 & $\square$\\
G5 & FNO surrogate $R^2>0.98$ & Phase 5 & $\square$\\
G6 & History match reduces RMSE 50\% & Phase 6 & $\square$\\
G7 & RL agent beats baseline 4\% & Phase 7 & $\square$\\
G8 & Lag-Llama fine-tune beats zero-shot 10\% & Phase 8 & $\square$\\
G9 & Agent runs SPE1 from natural language & Phase 9 & $\square$\\
G10 & FluidFlower/SPE11/Bunter/ETH pass & Phase 10 & $\square$\\
G11 & CI green on all platforms & Phase 11 & $\square$\\
G12 & v1.0 released & Phase 12 & $\square$\\
\bottomrule
\end{longtable}

% ==================================================================
\part{The Build Phases}
% ==================================================================

% ------------------------------------------------------------------
\section{Phase 0: Environment and Core Runtime}
\label{sec:phase0}
% ------------------------------------------------------------------

\subsection{Objective}
A clean Ubuntu workstation with Python, Julia, Octave/MATLAB, Docker, and PostgreSQL, all verified.

\subsection{Entry criteria}
A machine with Ubuntu 24.04 LTS (recommended), 8 cores, 32~GB RAM, 50~GB free disk.

\subsection{Step 0.1 --- Verify OS}

\stepID{0.1} Check the OS version.

\begin{lstlisting}[style=sh]
lsb_release -a
uname -r
\end{lstlisting}

\textbf{Expected output:}
\begin{lstlisting}[style=txt]
Description:    Ubuntu 24.04.x LTS
Release:        24.04
\end{lstlisting}

\textbf{If WSL2:} confirm systemd is enabled with \cmd{systemctl status}. If not, add to \file{/etc/wsl.conf}:
\begin{lstlisting}[style=txt]
[boot]
systemd=true
\end{lstlisting}
Then \cmd{wsl --shutdown} from Windows and restart.

\begin{failure}
If \cmd{lsb\_release} is not found: \cmd{sudo apt install lsb-release}.\\
If OS is not 24.04 LTS: rebuild on 24.04; OPM Flow 2026.04 supports 24.04 and 26.04 only.
\end{failure}

\begin{aicheckpoint}
Confirm OS is 24.04 LTS or 26.04 LTS. Confirm systemd is running. Ask: ``Is this a fresh machine or does it already have software installed that might conflict?''
\end{aicheckpoint}

\subsection{Step 0.2 --- Install system dependencies}

\stepID{0.2} Install the base packages.

\begin{lstlisting}[style=sh]
sudo apt update && sudo apt upgrade -y
sudo apt install -y \
    build-essential cmake git curl wget unzip \
    libboost-all-dev libopenblas-dev liblapack-dev \
    libhdf5-dev libfftw3-dev libsuitesparse-dev \
    python3-dev python3-venv python3-pip \
    postgresql postgresql-contrib redis-server \
    docker.io docker-compose-v2 \
    graphviz libgraphviz-dev pkg-config \
    lsb-release software-properties-common
\end{lstlisting}

\textbf{Expected output:} no errors, ends with the shell prompt.

\begin{failure}
\texttt{E: Unable to locate package}: run \cmd{sudo apt update} first.\\
\texttt{E: Could not get lock}: another apt process is running; wait or \cmd{sudo rm /var/lib/dpkg/lock}.\\
Disk full: free at least 50~GB.
\end{failure}

\subsection{Step 0.3 --- Enable Docker without sudo}

\stepID{0.3}
\begin{lstlisting}[style=sh]
sudo usermod -aG docker $USER
newgrp docker
docker run --rm hello-world
\end{lstlisting}

\textbf{Expected output:} ``Hello from Docker!'' message.

\begin{failure}
\texttt{permission denied while trying to connect}: log out and back in, then retry.\\
\texttt{Cannot connect to the Docker daemon}: \cmd{sudo systemctl start docker}.
\end{failure}

\subsection{Step 0.4 --- Create Python environment}

\stepID{0.4}
\begin{lstlisting}[style=sh]
python3 -m venv ~/petrolumen-env
source ~/petrolumen-env/bin/activate
pip install --upgrade pip setuptools wheel
\end{lstlisting}

\textbf{Expected output:} prompt shows \cmd{(petrolumen-env)}.

\begin{failure}
\texttt{ensurepip is not available}: \cmd{sudo apt install python3-venv}.
\end{failure}

\subsection{Step 0.5 --- Install Python scientific stack}

\stepID{0.5}
\begin{lstlisting}[style=sh]
pip install numpy scipy pandas xarray pyarrow \
    matplotlib seaborn plotly \
    scikit-learn torch torchvision torchaudio \
    transformers accelerate datasets \
    fastapi uvicorn pydantic pint \
    sqlalchemy alembic psycopg2-binary \
    pytest pytest-cov mypy ruff black \
    jupyterlab ipykernel
\end{lstlisting}

\textbf{Expected output:} all packages install successfully. Torch may take several minutes.

\begin{failure}
\texttt{ERROR: Could not find a version}: check internet; try \cmd{pip install --upgrade pip}.\\
Torch CUDA mismatch: if you have a GPU, install from \url{https://pytorch.org/get-started/locally/} with the correct CUDA version.
\end{failure}

\subsection{Step 0.6 --- Install Julia}

\stepID{0.6}
\begin{lstlisting}[style=sh]
curl -fsSL https://install.julialang.org | sh
# Restart shell, then:
julia -e 'using Pkg; Pkg.add(["Jutul", "JutulDarcy", "GeoEnergyIO", "CairoMakie"])'
\end{lstlisting}

\textbf{Expected output:} Julia 1.10+ installed; packages precompile without error.

\begin{failure}
\texttt{julia: command not found}: source the profile (\cmd{source ~/.bashrc}) or restart the terminal.\\
Precompilation fails: \cmd{sudo apt install libopenblas-dev liblapack-dev} and retry.
\end{failure}

\subsection{Step 0.7 --- Install Octave and MRST}

\stepID{0.7}
\begin{lstlisting}[style=sh]
sudo apt install -y octave
wget https://www.sintef.no/globalassets/project/mrst/download/mrst-2026a.zip
unzip mrst-2026a.zip -d ~/mrst
octave --eval "addpath(genpath('~/mrst')); mrstModule add core; disp('MRST OK')"
\end{lstlisting}

\textbf{Expected output:} \cmd{MRST OK}.

\begin{failure}
\texttt{addpath failed}: check \cmd{ls ~/mrst} shows the mrst folder.\\
\texttt{mrstModule not found}: path is \cmd{~/mrst/mrst}, adjust \cmd{addpath} accordingly.
\end{failure}

\subsection{Step 0.8 --- Install PostgreSQL}

\stepID{0.8}
\begin{lstlisting}[style=sh]
sudo systemctl enable --now postgresql
sudo -u postgres psql -c "CREATE DATABASE petrolumen;"
sudo -u postgres psql -c "CREATE USER petrolumen WITH PASSWORD 'petrolumen';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE petrolumen TO petrolumen;"
psql -U petrolumen -h localhost -d petrolumen -c "SELECT version();"
\end{lstlisting}

\textbf{Expected output:} PostgreSQL version string.

\begin{failure}
\texttt{Peer authentication failed}: use \cmd{sudo -u postgres psql} instead.\\
\texttt{Connection refused}: \cmd{sudo systemctl start postgresql}.
\end{failure}

\begin{gate}
\textbf{Gate G0:} Run all four checks:
\begin{lstlisting}[style=sh]
python -c "import torch, sklearn, fastapi; print('Python OK')"
julia -e 'using JutulDarcy; println("JutulDarcy OK")'
octave --eval "addpath(genpath('~/mrst')); mrstModule add core; disp('MRST OK')"
docker run --rm hello-world
psql -U petrolumen -h localhost -d petrolumen -c "SELECT 1;"
\end{lstlisting}
All five must print success. If any fails, return to the relevant step.
\end{gate}

\begin{aicheckpoint}
All of Gate G0 passed. Ask: ``Do you have a GPU? If yes, which model and CUDA version?'' Record the answer; it affects Phases 5--9.
\end{aicheckpoint}

% ------------------------------------------------------------------
\section{Phase 1: Simulation Engines}
\label{sec:phase1}
% ------------------------------------------------------------------

\subsection{Objective}
All four simulation engines installed and verified on the SPE1 benchmark.

\subsection{Entry criteria}
Gate G0 passed.

\subsection{Step 1.1 --- Install OPM Flow}

\stepID{1.1}
\begin{lstlisting}[style=sh]
sudo add-apt-repository ppa:opm/ppa
sudo apt update
sudo apt install -y libopm-simulators-bin
flow --version
\end{lstlisting}

\textbf{Expected output:} version 2026.04 or newer.

\begin{failure}
\texttt{Unable to locate package libopm-simulators-bin}: PPA not added; rerun \cmd{sudo add-apt-repository ppa:opm/ppa}.\\
\texttt{flow: command not found}: \cmd{sudo apt install opm-simulators} (alternative package name).
\end{failure}

\subsection{Step 1.2 --- Verify JutulDarcy}

\stepID{1.2}
\begin{lstlisting}[style=jl]
julia -e 'using JutulDarcy; println("JutulDarcy loaded OK")'
\end{lstlisting}

\textbf{Expected output:} \cmd{JutulDarcy loaded OK}.

\begin{failure}
Precompilation error: reinstall with \cmd{julia -e 'using Pkg; Pkg.rm("JutulDarcy"); Pkg.add("JutulDarcy")'}.
\end{failure}

\subsection{Step 1.3 --- Verify MRST}

\stepID{1.3}
\begin{lstlisting}[style=matlab]
octave --eval "addpath(genpath('~/mrst')); mrstModule add ad-blackoil; disp('ad-blackoil OK')"
\end{lstlisting}

\textbf{Expected output:} \cmd{ad-blackoil OK}.

\subsection{Step 1.4 --- Install open-DARTS}

\stepID{1.4}
\begin{lstlisting}[style=sh]
pip install open-darts
python -c "import darts; print(darts.__version__)"
\end{lstlisting}

\textbf{Expected output:} version string.

\begin{failure}
\texttt{No matching distribution}: open-DARTS requires Python 3.10--3.13. Check \cmd{python --version}.\\
Install fails on build: \cmd{sudo apt install -y libgomp1 libmpich-dev}; retry.
\end{failure}

\subsection{Step 1.5 --- Download OPM benchmark data}

\stepID{1.5}
\begin{lstlisting}[style=sh]
git clone https://github.com/OPM/opm-data.git ~/opm-data
ls ~/opm-data
\end{lstlisting}

\textbf{Expected output:} directories \cmd{spe1}, \cmd{spe9}, \cmd{spe10}, \cmd{norne}.

\begin{failure}
Clone is slow: use \cmd{git clone --depth 1} to fetch only the latest.
\end{failure}

\subsection{Step 1.6 --- Run SPE1 on OPM Flow}

\stepID{1.6}
\begin{lstlisting}[style=sh]
cd ~/opm-data/spe1
flow SPE1.DATA 2>&1 | tee spe1.log
ls
\end{lstlisting}

\textbf{Expected output:} \cmd{SPE1.SMSPEC}, \cmd{SPE1.UNSMRY}, \cmd{SPE1.EGRID} files. Log ends with ``Simulation complete''.

\begin{failure}
\texttt{flow: command not found}: reinstall (Step 1.1).\\
Simulation stalls: check CPU count with \cmd{nproc}; run with \cmd{flow --threads-per-process=4 SPE1.DATA}.
\end{failure}

\subsection{Step 1.7 --- Run SPE1 on JutulDarcy}

\stepID{1.7}
\begin{lstlisting}[style=jl]
using JutulDarcy, GeoEnergyIO
data = parse_data_file(joinpath(homedir(), "opm-data", "spe1", "SPE1.DATA"))
model, state0, dt = setup_reservoir_model(data)
result = simulate_reservoir(state0, model, dt)
println("JutulDarcy SPE1 complete")
\end{lstlisting}

\textbf{Expected output:} \cmd{JutulDarcy SPE1 complete}.

\begin{failure}
Parse error: the deck may use keywords JutulDarcy does not support; this is fine --- the goal is a successful run, not an identical one.
\end{failure}

\begin{gate}
\textbf{Gate G1:} The SPE1 run on OPM Flow and on JutulDarcy both complete. Extract cumulative oil production from each:
\begin{lstlisting}[style=sh]
# OPM Flow summary
python -c "
from opm.io.ecl import ESmry
s = ESmry('~/opm-data/spe1/SPE1.SMSPEC')
print('FOPT final:', s['FOPT'][-1])
"
\end{lstlisting}
Both engines must report FOPT within 2\% of 1.0$\times 10^6$~Sm$^3$ (SPE1 reference).
\end{gate}

\begin{aicheckpoint}
Both engines ran SPE1. Ask: ``Did the FOPT values agree within 2\%? If not, paste both values and we will diagnose before continuing.''
\end{aicheckpoint}

% ------------------------------------------------------------------
\section{Phase 2: Engineering Calculation Libraries}
\label{sec:phase2}
% ------------------------------------------------------------------

\subsection{Objective}
All seven engineering libraries installed and individually tested.

\subsection{Entry criteria}
Gate G1 passed.

\subsection{Step 2.1 --- pyResToolbox}

\stepID{2.1}
\begin{lstlisting}[style=sh]
pip install pyrestoolbox
python -c "
from pyrestoolbox import pyrestoolbox as rtb
rs = rtb.rs_standing(psia=3000, t=180, api=35, gamma_g=0.75)
print(f'Rs = {rs:.2f} scf/STB')
"
\end{lstlisting}

\textbf{Expected output:} \cmd{Rs = ~600--700 scf/STB} (order of magnitude).

\begin{failure}
\texttt{ImportError}: package name may be \cmd{pyrestoolbox} or \cmd{pyResToolbox}; try both.
\end{failure}

\subsection{Step 2.2 --- welltest-pta}

\stepID{2.2}
\begin{lstlisting}[style=sh]
pip install welltest-pta
python -c "from welltest_pta import WellTest; print('welltest-pta OK')"
\end{lstlisting}

\textbf{Expected output:} \cmd{welltest-pta OK}.

\subsection{Step 2.3 --- GeostatsPy}

\stepID{2.3}
\begin{lstlisting}[style=sh]
pip install geostatspy
python -c "import geostatspy.geostats; print('GeostatsPy OK')"
\end{lstlisting}

\textbf{Expected output:} \cmd{GeostatsPy OK}.

\begin{failure}
\texttt{ModuleNotFoundError: numba}: \cmd{pip install numba}.
\end{failure}

\subsection{Step 2.4 --- Petres}

\stepID{2.4}
\begin{lstlisting}[style=sh]
pip install petres
python -c "from petres.grids import CornerPointGrid; print('Petres OK')"
\end{lstlisting}

\textbf{Expected output:} \cmd{Petres OK}.

\subsection{Step 2.5 --- resqpy}

\stepID{2.5}
\begin{lstlisting}[style=sh]
pip install resqpy
python -c "import resqpy.model as rq; print('resqpy OK')"
\end{lstlisting}

\textbf{Expected output:} \cmd{resqpy OK}.

\subsection{Step 2.6 --- pycopm}

\stepID{2.6}
\begin{lstlisting}[style=sh]
pip install pycopm
pycopm --help
\end{lstlisting}

\textbf{Expected output:} usage message.

\begin{failure}
\texttt{command not found}: verify the pip environment is active (\cmd{which pycopm}).
\end{failure}

\subsection{Step 2.7 --- Write the calculation test module}

\stepID{2.7} Create \file{~/petrolumen/tests/test\_calculations.py} with one test per library:

\begin{lstlisting}[caption={tests/test\_calculations.py}]
def test_pyrestoolbox():
    from pyrestoolbox import pyrestoolbox as rtb
    assert rtb.rs_standing(psia=3000, t=180, api=35, gamma_g=0.75) > 0

def test_welltest_pta():
    from welltest_pta import WellTest
    assert WellTest is not None

def test_geostatspy():
    import geostatspy.geostats
    assert geostatspy.geostats is not None

def test_petres():
    from petres.grids import CornerPointGrid
    assert CornerPointGrid is not None

def test_resqpy():
    import resqpy.model
    assert resqpy.model is not None

def test_pycopm():
    import subprocess
    assert subprocess.run(["pycopm", "--help"], capture_output=True).returncode == 0
\end{lstlisting}

Then:
\begin{lstlisting}[style=sh]
cd ~/petrolumen
pytest tests/test_calculations.py -v
\end{lstlisting}

\textbf{Expected output:} 6 passed.

\begin{gate}
\textbf{Gate G2:} All 6 tests pass.
\end{gate}

\begin{aicheckpoint}
All engineering libraries verified. Ask: ``Which of these libraries do you anticipate using most heavily? I can then point you to the most relevant example code in each.''
\end{aicheckpoint}

% ------------------------------------------------------------------
\section{Phase 3: Data Model and API Skeleton}
\label{sec:phase3}
% ------------------------------------------------------------------

\subsection{Objective}
A running FastAPI service backed by PostgreSQL that can create a project, create a case from SPE1, run it, and return summary results as Parquet.

\subsection{Entry criteria}
Gate G2 passed.

\subsection{Step 3.1 --- Define the minimum schema}

\stepID{3.1} Create \file{~/petrolumen/sql/schema.sql}:

\begin{lstlisting}[style=sql]
CREATE SCHEMA IF NOT EXISTS reservoir;

CREATE TABLE reservoir.project (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    units TEXT NOT NULL DEFAULT 'SI',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE reservoir.case (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID NOT NULL REFERENCES reservoir.project(id),
    name TEXT NOT NULL,
    engine TEXT NOT NULL,
    deck_path TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE reservoir.run (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    case_id UUID NOT NULL REFERENCES reservoir.case(id),
    status TEXT NOT NULL DEFAULT 'queued',
    exit_code INT,
    result_uri TEXT,
    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ
);
\end{lstlisting}

Apply:
\begin{lstlisting}[style=sh]
psql -U petrolumen -h localhost -d petrolumen -f ~/petrolumen/sql/schema.sql
\end{lstlisting}

\textbf{Expected output:} \cmd{CREATE SCHEMA}, \cmd{CREATE TABLE} $\times3$.

\subsection{Step 3.2 --- pydantic models}

\stepID{3.2} Create \file{~/petrolumen/src/petrolumen/core/models.py}:

\begin{lstlisting}
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID
from pydantic import BaseModel

class RunStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"

class Project(BaseModel):
    id: UUID
    name: str
    units: str = "SI"
    created_at: datetime

class Case(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    engine: str
    deck_path: Optional[str]

class Run(BaseModel):
    id: UUID
    case_id: UUID
    status: RunStatus
    exit_code: Optional[int]
    result_uri: Optional[str]
\end{lstlisting}

\subsection{Step 3.3 --- FastAPI app}

\stepID{3.3} Create \file{~/petrolumen/src/petrolumen/api/main.py}:

\begin{lstlisting}
from fastapi import FastAPI, HTTPException
import subprocess, uuid, os
from pathlib import Path
from .db import get_db

app = FastAPI(title="PetroLumen Reservoir API")

@app.post("/v1/projects")
def create_project(name: str):
    ... # INSERT and return

@app.post("/v1/cases")
def create_case(project_id: str, name: str, deck_path: str, engine: str = "opm_flow"):
    ... # INSERT and return

@app.post("/v1/runs")
def create_run(case_id: str):
    ... # INSERT, spawn worker, return

@app.get("/v1/runs/{run_id}")
def get_run(run_id: str):
    ... # SELECT and return
\end{lstlisting}

Run the server:
\begin{lstlisting}[style=sh]
uvicorn petrolumen.api.main:app --host 0.0.0.0 --port 8000
\end{lstlisting}

\textbf{Expected output:} \cmd{Uvicorn running on http://0.0.0.0:8000}.

\subsection{Step 3.4 --- Worker}

\stepID{3.4} The worker receives a \cmd{run\_id}, reads the \cmd{case.deck\_path}, runs \cmd{flow <deck>} as a subprocess, parses \cmd{.SMSPEC} to Parquet, updates the \cmd{run} row. Use a simple thread pool first; replace with Celery later.

\subsection{Step 3.5 --- Test end-to-end}

\stepID{3.5}
\begin{lstlisting}[style=sh]
# Create project
curl -X POST http://localhost:8000/v1/projects -d '{"name":"test"}' -H "Content-Type: application/json"

# Create case (use SPE1)
curl -X POST http://localhost:8000/v1/cases \
  -d '{"project_id":"<id>","name":"spe1","deck_path":"'$HOME'/opm-data/spe1/SPE1.DATA","engine":"opm_flow"}' \
  -H "Content-Type: application/json"

# Create run
curl -X POST http://localhost:8000/v1/runs -d '{"case_id":"<id>"}' -H "Content-Type: application/json"

# Poll
curl http://localhost:8000/v1/runs/<run_id>
\end{lstlisting}

\textbf{Expected output:} \cmd{status} transitions queued $\to$ running $\to$ succeeded, and \cmd{result\_uri} points to a Parquet file with FOPR, FOPT, WBHP.

\begin{gate}
\textbf{Gate G3:} The Parquet file exists, contains the three time series, and the run status is \cmd{succeeded}.
\end{gate}

\begin{aicheckpoint}
The API runs SPE1 end-to-end. Ask: ``Would you like to extend the schema with \cmd{well}, \cmd{fluid\_model}, and \cmd{schedule} tables before Phase 4, or proceed with the minimum schema?''
\end{aicheckpoint}

% ------------------------------------------------------------------
\section{Phase 4: Benchmark Validation Suite}
\label{sec:phase4}
% ------------------------------------------------------------------

\subsection{Objective}
SPE1, SPE9, SPE10, and Norne all pass in automated tests, producing a defensible classical workbench.

\subsection{Entry criteria}
Gate G3 passed.

\subsection{Step 4.1 --- SPE1 regression test}

\stepID{4.1} Create \file{~/petrolumen/tests/test\_benchmarks.py}:

\begin{lstlisting}
import pytest, subprocess, tempfile, shutil
from pathlib import Path

SPE1 = Path.home() / "opm-data" / "spe1" / "SPE1.DATA"
REF_FOPT = 1.0e6  # SPE1 reference, adjust to units in the deck

@pytest.mark.benchmark
def test_spe1(tmp_path):
    deck = tmp_path / "SPE1.DATA"
    shutil.copy(SPE1, deck)
    r = subprocess.run(["flow", deck.name], cwd=tmp_path,
                       capture_output=True, text=True, timeout=600)
    assert r.returncode == 0, r.stderr
    from opm.io.ecl import ESmry
    s = ESmry(str(tmp_path / "SPE1.SMSPEC"))
    assert abs(s["FOPT"][-1] - REF_FOPT) / REF_FOPT < 0.02
\end{lstlisting}

Run:
\begin{lstlisting}[style=sh]
pytest tests/test_benchmarks.py::test_spe1 -v
\end{lstlisting}

\textbf{Expected output:} 1 passed.

\subsection{Step 4.2 --- Repeat for SPE9, SPE10, Norne}

\stepID{4.2} Add one test function per benchmark, following the SPE1 pattern. Use the reference FOPT/FWCT values published with each benchmark. Gates:

\begin{longtable}{@{}p{2cm}p{4cm}p{6cm}@{}}
\toprule
Benchmark & Physics & Gate\\
\midrule
SPE1 & Three-phase, gas coning & BHP and gas rate within 2\%\\
SPE9 & 26 wells, faulted & Cumulative production within 2\%\\
SPE10 & 60$\times$220$\times$85 heterogeneous & Water-cut within 3\%; deterministic across runs\\
Norne & Real field & Summary vectors within agreed tolerance\\
\bottomrule
\end{longtable}

\subsection{Step 4.3 --- Determinism test}

\stepID{4.3} Add a test that runs SPE1 twice and asserts bitwise-identical FOPT:

\begin{lstlisting}
def test_spe1_determinism(tmp_path):
    run1 = run_spe1(tmp_path / "a")
    run2 = run_spe1(tmp_path / "b")
    assert run1["FOPT"] == run2["FOPT"]
\end{lstlisting}

\begin{gate}
\textbf{Gate G4:} All four benchmark tests pass, and determinism holds. Tag the release: \cmd{git tag v0.1.0-classical}.
\end{gate}

\begin{aicheckpoint}
The classical workbench is now defensible. Confirm with the user: ``SPE1, SPE9, SPE10, and Norne all pass. This is the first major milestone. Would you like to commit and tag before Phase 5, or continue straight through?''
\end{aicheckpoint}

% ------------------------------------------------------------------
\section{Phase 5: AI Surrogates --- FNO/PINO for Norne}
\label{sec:phase5}
% ------------------------------------------------------------------

\subsection{Objective}
A trained Fourier Neural Operator surrogate that replaces OPM Flow inside a forecasting loop with $R^2 > 0.98$ and $10^4\times$ speedup.

\subsection{Entry criteria}
Gate G4 passed; GPU with 16--24~GB VRAM recommended.

\subsection{Step 5.1 --- Clone PhysicsNeMo Norne pipeline}

\stepID{5.1}
\begin{lstlisting}[style=sh]
git clone https://github.com/NVIDIA/physicsnemo.git ~/physicsnemo
cd ~/physicsnemo/examples/reservoir_simulation/norne
ls
\end{lstlisting}

\textbf{Expected output:} \cmd{src/}, \cmd{scripts/}, \cmd{conf/}, \cmd{README.md}.

\subsection{Step 5.2 --- Install dependencies}

\stepID{5.2}
\begin{lstlisting}[style=sh]
pip install -r requirements.txt
pip install physicsnemo
\end{lstlisting}

\begin{failure}
CUDA not found: \cmd{pip install torch --index-url https://download.pytorch.org/whl/cu121} (adjust for your CUDA version).
\end{failure}

\subsection{Step 5.3 --- Prepare Norne data}

\stepID{5.3} Download the Norne benchmark from Zenodo (DOI: \url{10.5281/zenodo.8062997}) or use the packaged data in PhysicsNeMo. Place under \file{\textasciitilde/physicsnemo/examples/reservoir\_simulation/norne/data/}.

\subsection{Step 5.4 --- Train the FNO surrogate}

\stepID{5.4}
\begin{lstlisting}[style=sh]
python src/Forward_problem_PINO.py --config conf/norne_fno.yaml 2>&1 | tee train.log
\end{lstlisting}

\textbf{Expected output:} training loss decreases; checkpoints saved. Training may take hours to a day depending on GPU.

\begin{failure}
CUDA out of memory: reduce batch size in the config.\\
NaN in loss: lower learning rate to \cmd{1e-4}.
\end{failure}

\subsection{Step 5.5 --- Validate}

\stepID{5.5}
\begin{lstlisting}[style=sh]
python src/evaluate_fno.py --checkpoint checkpoints/best.pt --test-data data/norne_test
\end{lstlisting}

\textbf{Expected output:} $R^2 > 0.98$ on oil production; relative error $<5\%$ on cumulative production.

\begin{gate}
\textbf{Gate G5:} $R^2 > 0.98$, relative error $<5\%$, inference $<1$~s/timestep.
\end{gate}

\begin{aicheckpoint}
FNO trained and validated. Ask: ``Would you like to integrate the surrogate into the API now, or proceed to Phase 6 and integrate later?''
\end{aicheckpoint}

% ------------------------------------------------------------------
\section{Phase 6: Differentiable UQ and History Matching}
\label{sec:phase6}
% ------------------------------------------------------------------

\subsection{Objective}
Adjoint gradients from JutulDarcy and an ES-MDA implementation that reduces history-matching RMSE by at least 50\% on SPE1.

\subsection{Entry criteria}
Gate G5 passed.

\subsection{Step 6.1 --- JutulDarcy SPE1 adjoint}

\stepID{6.1}
\begin{lstlisting}[style=jl]
using Jutul, JutulDarcy, GeoEnergyIO
# Follow examples/data_assimilation/spe1_gradients.jl
# in the JutulDarcy repository
\end{lstlisting}

Confirm the gradient matches finite differences to within $10^{-4}$ relative error.

\subsection{Step 6.2 --- ES-MDA}

\stepID{6.2} Implement the ES-MDA update from Appendix~B. Test on SPE1 with 100 ensemble members and 4 assimilation steps.

\subsection{Step 6.3 --- Validate}

\stepID{6.3} Prior ensemble RMSE vs. posterior ensemble RMSE. Posterior must be $\geq 50\%$ lower.

\begin{gate}
\textbf{Gate G6:} Posterior RMSE $\leq 0.5 \times$ prior RMSE; posterior re-run with OPM Flow matches observations within measurement error.
\end{gate}

% ------------------------------------------------------------------
\section{Phase 7: Reinforcement Learning for Control}
\label{sec:phase7}
% ------------------------------------------------------------------

\subsection{Objective}
A TD3 agent that achieves at least 4\% NPV improvement over a reactive baseline on a 2D waterflood case.

\subsection{Entry criteria}
Gate G6 passed.

\subsection{Step 7.1 --- Clone DRL\_CLRM}

\stepID{7.1}
\begin{lstlisting}[style=sh]
git clone https://github.com/yus-nas/DRL_CLRM.git ~/DRL_CLRM
cd ~/DRL_CLRM
pip install -r requirements.txt
\end{lstlisting}

\subsection{Step 7.2 --- Train TD3}

\stepID{7.2}
\begin{lstlisting}
from stable_baselines3 import TD3
from petrolumen.rl import ReservoirEnv

env = ReservoirEnv(case, surrogate=fno_surrogate)
model = TD3("MlpPolicy", env, learning_rate=3e-4,
            buffer_size=1_000_000, batch_size=256,
            gamma=0.99, tau=0.005, policy_delay=2)
model.learn(total_timesteps=1_000_000)
model.save("td3_reservoir_agent")
\end{lstlisting}

\subsection{Step 7.3 --- Validate}

\stepID{7.3} Run the trained agent on a 2D waterflood case. Compare NPV against a reactive baseline.

\begin{gate}
\textbf{Gate G7:} NPV improvement $\geq 4\%$ over baseline, and within 10\% of the published DRL\_CLRM result (15\% for 2D).
\end{gate}

% ------------------------------------------------------------------
\section{Phase 8: Foundation-Model Forecasting}
\label{sec:phase8}
% ------------------------------------------------------------------

\subsection{Objective}
A Lag-Llama forecaster that beats zero-shot by at least 10\% MAE after fine-tuning on analog wells.

\subsection{Entry criteria}
Gate G7 passed.

\subsection{Step 8.1 --- Install Lag-Llama}

\stepID{8.1}
\begin{lstlisting}[style=sh]
git clone https://github.com/time-series-foundation-models/lag-llama.git ~/lag-llama
cd ~/lag-llama
pip install -r requirements.txt
\end{lstlisting}

\subsection{Step 8.2 --- Zero-shot forecast}

\stepID{8.2} Feed production history to the pre-trained model, generate a probabilistic forecast, compute MAE on held-out wells.

\subsection{Step 8.3 --- Fine-tune}

\stepID{8.3} Fine-tune on analog wells with a small learning rate and early stopping.

\begin{gate}
\textbf{Gate G8:} Fine-tuned MAE $\leq 0.9 \times$ zero-shot MAE on held-out wells.
\end{gate}

% ------------------------------------------------------------------
\section{Phase 9: Agentic Workflows}
\label{sec:phase9}
% ------------------------------------------------------------------

\subsection{Objective}
An AI agent that can run SPE1 from natural language, with a complete audit log.

\subsection{Entry criteria}
Gate G8 passed.

\subsection{Step 9.1 --- pyResToolbox MCP server}

\stepID{9.1}
\begin{lstlisting}[style=sh]
git clone https://github.com/gabrielserrao/pyrestoolbox-mcp.git ~/pyrestoolbox-mcp
cd ~/pyrestoolbox-mcp
pip install -e .
python -m pyrestoolbox_mcp.server  # verify it starts
\end{lstlisting}

\subsection{Step 9.2 --- Configure MCP client}

\stepID{9.2} In the MCP client (Claude Desktop, Cursor, or custom), add:

\begin{lstlisting}[style=txt]
{
  "mcpServers": {
    "pyrestoolbox": {
      "command": "python",
      "args": ["-m", "pyrestoolbox_mcp.server"]
    }
  }
}
\end{lstlisting}

\subsection{Step 9.3 --- Safety layer}

\stepID{9.3} Implement:

\begin{enumerate}[leftmargin=1.4em]
  \item schema-validated tools;
  \item sandboxed execution (Docker, CPU/memory limits);
  \item audit log to PostgreSQL.
\end{enumerate}

\subsection{Step 9.4 --- Validation}

\stepID{9.4} Natural-language prompt: ``Run SPE1, report cumulative oil at 365 days, and compare with the reference.''

\begin{gate}
\textbf{Gate G9:} Agent selects the correct tool, runs the simulation, returns a value within 2\% of reference, and the audit log shows the full chain.
\end{gate}

% ------------------------------------------------------------------
\section{Phase 10: Energy-Transition Physics}
\label{sec:phase10}
% ------------------------------------------------------------------

\subsection{Objective}
CO$_2$, H$_2$, and geothermal benchmarks all pass.

\subsection{Entry criteria}
Gate G9 passed.

\subsection{Step 10.1 --- CO$_2$: FluidFlower}

\stepID{10.1}
\begin{lstlisting}[style=sh]
pip install pofff
python -c "import pofff; print('pofff OK')"
\end{lstlisting}

Run the FluidFlower history-matching workflow. Gate: Wasserstein distance below published threshold; visual plume match.

\subsection{Step 10.2 --- CO$_2$: SPE11 Case B}

\stepID{10.2}
\begin{lstlisting}[style=sh]
flow spe11b.DATA
\end{lstlisting}

Compare against published reference (DOI: 10.18419/DARUS-4750). Gate: convergence and visual plume match.

\subsection{Step 10.3 --- H$_2$: open-DARTS Bunter}

\stepID{10.3}
\begin{lstlisting}[style=sh]
git clone https://gitlab.com/open-darts/h2-bunter.git ~/h2-bunter
cd ~/h2-bunter
python main_run.py --model bunter_1p2c_reference --cycles 10
\end{lstlisting}

Gate: H$_2$ recovery efficiency and CH$_4$ contamination within ensemble range.

\subsection{Step 10.4 --- Geothermal: ETH EDFM}

\stepID{10.4} Install the ETH MRST module, run the four benchmark cases. Gate: relative error $<1\%$.

\begin{gate}
\textbf{Gate G10:} All four energy-transition benchmarks pass.
\end{gate}

% ------------------------------------------------------------------
\section{Phase 11: Testing and Quality Assurance}
\label{sec:phase11}
% ------------------------------------------------------------------

\subsection{Objective}
CI is green on all supported platforms; the Docker image runs SPE1 on a clean machine.

\subsection{Entry criteria}
Gate G10 passed.

\subsection{Step 11.1 --- Test pyramid}

\stepID{11.1} Ensure tests exist for:

\begin{longtable}{@{}p{3cm}p{4cm}p{6cm}@{}}
\toprule
Layer & Tool & Gate\\
\midrule
Unit & pytest & $>$90\% coverage\\
Integration & pytest + Docker & All API endpoints end-to-end\\
Benchmarks & pytest markers & SPE1/SPE9/SPE10/Norne every release\\
AI surrogates & pytest & $R^2 > 0.98$\\
Agentic & pytest + mock LLM & 20 golden prompts\\
Energy transition & pytest & All four benchmarks\\
\bottomrule
\end{longtable}

\subsection{Step 11.2 --- Static analysis}

\stepID{11.2}
\begin{lstlisting}[style=sh]
ruff check src/
black --check src/
mypy --strict src/petrolumen/core/
\end{lstlisting}

\subsection{Step 11.3 --- CI pipeline}

\stepID{11.3} Use GitHub Actions or GitLab CI. Matrix: Ubuntu 24.04/26.04, Python 3.11/3.12/3.13, with/without GPU.

\subsection{Step 11.4 --- Docker image}

\stepID{11.4} Build an image that bundles OPM Flow, JutulDarcy, MRST, and the Python stack.

\begin{gate}
\textbf{Gate G11:} CI green on all matrix entries; the Docker image runs SPE1 successfully on a clean VM.
\end{gate}

% ------------------------------------------------------------------
\section{Phase 12: Documentation and Distribution}
\label{sec:phase12}
% ------------------------------------------------------------------

\subsection{Objective}
PetroLumen v1.0 released on PyPI and Docker Hub, with complete documentation and a validation report.

\subsection{Entry criteria}
Gate G11 passed.

\subsection{Step 12.1 --- Physics docs}

\stepID{12.1} Every equation links to a reference. Generate a \file{docs/physics/} folder.

\subsection{Step 12.2 --- API docs}

\stepID{12.2} Auto-generate from FastAPI OpenAPI. Publish at \file{/docs}.

\subsection{Step 12.3 --- User guide}

\stepID{12.3} One worked example per module: SPE1 (classical), Norne (FNO), FluidFlower (CO$_2$), Bunter (H$_2$), ETH (geothermal).

\subsection{Step 12.4 --- Validation report}

\stepID{12.4} Generate a PDF with:

\begin{itemize}[leftmargin=1.4em]
  \item SPE1/SPE9/SPE10/Norne comparison plots;
  \item FNO $R^2$ and error metrics;
  \item FluidFlower Wasserstein distance;
  \item Bunter H$_2$ recovery statistics.
\end{itemize}

\subsection{Step 12.5 --- Package}

\stepID{12.5}
\begin{lstlisting}[style=sh]
pip install petrolumen[classical]      # OPM Flow + Python only
pip install petrolumen[ai]            # + PyTorch, transformers
pip install petrolumen[full]          # + GPL engines
docker pull petrolumen/petrolumen:latest
\end{lstlisting}

\begin{gate}
\textbf{Gate G12:} A new user can install PetroLumen, run SPE1, and reproduce the reference in under 30 minutes.
\end{gate}

% ------------------------------------------------------------------
\section{Phase 13: Continuous Operation}
\label{sec:phase13}
% ------------------------------------------------------------------

\subsection{Objective}
Sustained improvement: quarterly releases, benchmark monitoring, ecosystem tracking.

\subsection{Quarterly cadence}

\begin{longtable}{@{}p{2cm}p{11cm}@{}}
\toprule
Quarter & Focus\\
\midrule
Q1 & Classical workbench: Phases 0--4\\
Q2 & AI surrogates and UQ: Phases 5--6\\
Q3 & RL, forecasting, agents: Phases 7--9\\
Q4 & Energy transition and hardening: Phases 10--12\\
\bottomrule
\end{longtable}

\subsection{What to monitor}

\begin{itemize}[leftmargin=1.4em]
  \item OPM Flow quarterly releases; pin versions, re-run benchmarks.
  \item JutulDarcy adjoint and history-matching changes.
  \item PhysicsNeMo Norne pipeline updates.
  \item New MCP servers: audit before integrating.
  \item FluidFlower and SPE11 dataset DOIs.
\end{itemize}

% ==================================================================
\part{Appendices}
% ==================================================================

% ------------------------------------------------------------------
\section{Appendix A: Master Command Reference}
% ------------------------------------------------------------------

\begin{longtable}{@{}p{2.4cm}p{4.2cm}p{6cm}@{}}
\toprule
Step & Command & Purpose\\
\midrule
\endhead
0.2 & \cmd{sudo apt install -y ...} & Base packages\\
0.4 & \cmd{python3 -m venv ...} & Python env\\
0.6 & \cmd{julia -e 'using Pkg; ...'} & JutulDarcy install\\
0.7 & \cmd{octave --eval "..."} & MRST verify\\
0.8 & \cmd{psql -U petrolumen ...} & DB verify\\
1.1 & \cmd{sudo apt install -y libopm-simulators-bin} & OPM Flow\\
1.5 & \cmd{git clone .../opm-data} & Benchmarks\\
2.1 & \cmd{pip install pyrestoolbox} & PVT library\\
2.2 & \cmd{pip install welltest-pta} & PTA library\\
2.3 & \cmd{pip install geostatspy} & Geostats\\
2.4 & \cmd{pip install petres} & Grids\\
2.5 & \cmd{pip install resqpy} & RESQML\\
2.6 & \cmd{pip install pycopm} & Mesh coarsening\\
3.1 & \cmd{psql -f schema.sql} & DB schema\\
3.3 & \cmd{uvicorn ...} & API server\\
4.1 & \cmd{pytest test_benchmarks.py} & Regression tests\\
5.1 & \cmd{git clone .../physicsnemo} & FNO Norne\\
5.4 & \cmd{python Forward_problem_PINO.py} & FNO training\\
6.1 & JutulDarcy adjoint example & Gradients\\
7.1 & \cmd{git clone .../DRL_CLRM} & RL reference\\
8.1 & \cmd{git clone .../lag-llama} & Foundation model\\
9.1 & \cmd{pip install -e pyrestoolbox-mcp} & MCP server\\
10.1 & \cmd{pip install pofff} & FluidFlower\\
10.2 & \cmd{flow spe11b.DATA} & SPE11\\
10.3 & \cmd{python main_run.py} & H$_2$ Bunter\\
11.3 & CI YAML & Pipeline\\
12.5 & \cmd{pip install petrolumen[...]} & Release\\
\bottomrule
\end{longtable}

% ------------------------------------------------------------------
\section{Appendix B: ES-MDA Reference Implementation}
% ------------------------------------------------------------------

\begin{lstlisting}[caption={ES-MDA update (NumPy).}]
import numpy as np

def es_mda_update(M, D, d_obs, Cd, alpha, R=None):
    """
    M: (Ne, Nm) ensemble of model parameters
    D: (Ne, Nd) ensemble of predicted data
    d_obs: (Nd,) observed data
    Cd: (Nd, Nd) observation error covariance
    alpha: scalar inflation coefficient
    R: (Nm, Nd) localization matrix or None
    """
    Ne = M.shape[0]
    Cmd = np.cov(M.T, D.T)[:M.shape[1], M.shape[1]:]
    Cdd = np.cov(D.T)
    K = Cmd @ np.linalg.inv(Cdd + alpha * Cd)
    if R is not None:
        K = R * K
    noise = np.random.multivariate_normal(
        np.zeros(D.shape[1]), alpha * Cd, size=Ne
    )
    return M + (K @ (d_obs - D + noise).T).T
\end{lstlisting}

% ------------------------------------------------------------------
\section{Appendix C: Book-to-Module Mapping}
% ------------------------------------------------------------------

\begin{longtable}{@{}p{4.4cm}p{3.6cm}p{5.0cm}@{}}
\toprule
Book & Module & Implementation path\\
\midrule
\endhead
Dake, \emph{Fundamentals} & Fluids, volumetrics, MatBal & pyResToolbox + custom; validate on SPE1/SPE9\\
Dake, \emph{Practice} & Workflow, judgment & UI guidance and warnings\\
Ahmed, \emph{Handbook} & Correlations, water influx & Cross-check pyResToolbox\\
McCain, \emph{Properties} & PVT, lab matching & Spec for fluids module; custom EOS tuning\\
Lie, \emph{MRST Intro} & Simulation architecture & Plugin contract around MRST\\
Peaceman, \emph{Numerical} & Discretisation, solvers & Validate against analytical\\
Pyrcz, \emph{Geostats Python} & Geostats & Follow e-book; GeostatsPy\\
Pyrcz, \emph{Applied ML} & Surrogates & ML curriculum; PyTorch\\
Horne, \emph{Well Test} & PTA & welltest-pta + custom\\
Ganat, \emph{Modern PTA} & Special cases & Layered, fractured, horizontal\\
Lee \& Wattenbarger & Gas MatBal, $p/Z$ & Implement; test on gas\\
Guo, \emph{Production} & Nodal & pynodal or custom\\
Wheaton, \emph{Economics} & Economics & NPV/IRR; judgment human\\
Satter et al. & EOR screening & Advisory, not automatic\\
Newman, \emph{Modern} & CO$_2$, unconventional & Phase 10 spec\\
Islam et al. & Emulators & FNO/PINN\\
SPEE Monograph 4 & Unconventional & Probabilistic DCA\\
\bottomrule
\end{longtable}

% ------------------------------------------------------------------
\section{Appendix D: Licensing Boundaries}
% ------------------------------------------------------------------

\begin{longtable}{@{}p{3.6cm}p{2.6cm}p{7.0cm}@{}}
\toprule
Component & Licence & Rule\\
\midrule
OPM Flow & OSL-3.0 / GPL & External executable only\\
JutulDarcy.jl & MIT & Direct import or subprocess\\
MRST & GPL-3.0 & External process only\\
open-DARTS & Open source & Direct; check modules\\
pyResToolbox & GPL-3.0 & Optional extra or subprocess\\
pyResToolbox MCP & GPL-3.0 & Optional agent layer\\
resqpy & Apache-2.0 & Direct import\\
Petres & LGPL & Direct; dynamic linking\\
GeostatsPy & MIT & Direct import\\
welltest-pta & MIT & Direct import\\
Lag-Llama & Apache-2.0 & Direct import\\
DRL\_CLRM & Open source & Reference; re-implement\\
\bottomrule
\end{longtable}

Ship under Apache-2.0 or MIT. Declare GPL engines as optional backends.

% ------------------------------------------------------------------
\section{Appendix E: Compute Requirements}
% ------------------------------------------------------------------

\begin{longtable}{@{}p{3cm}p{2.4cm}p{2cm}p{2.6cm}p{3cm}@{}}
\toprule
Phase & CPU & RAM & GPU & Storage\\
\midrule
0--4 & 8 cores & 32 GB & none & 50 GB\\
5 (FNO) & 16 cores & 64 GB & 24 GB VRAM & 200 GB\\
6--7 & 16 cores & 64 GB & optional & 200 GB\\
8--9 & 8 cores & 32 GB & 16 GB VRAM & 100 GB\\
10 & 16 cores & 64 GB & optional & 500 GB\\
\bottomrule
\end{longtable}

% ------------------------------------------------------------------
\section{Appendix F: Global Troubleshooting}
% ------------------------------------------------------------------

\begin{longtable}{@{}p{4.4cm}p{4.4cm}p{4.4cm}@{}}
\toprule
Symptom & Likely cause & Fix\\
\midrule
\endhead
\cmd{flow: not found} & PPA not added & \cmd{sudo apt update \&\& sudo apt install libopm-simulators-bin}\\
JutulDarcy precompile hangs & Missing libs & \cmd{sudo apt install libopenblas-dev liblapack-dev}\\
MRST module missing & Path wrong & \cmd{addpath(genpath('~/mrst'))}\\
open-DARTS install fails & Python version & Use Python 3.10--3.13\\
MCP tools not visible & Server not started & Verify with \cmd{python -m pyrestoolbox\_mcp.server}\\
FNO diverges & LR too high & Set \cmd{lr=1e-4}\\
Lag-Llama poor & Context too short & Use 64--128 context\\
pycopm fails & OPM too old & Upgrade to 2024.10+\\
PostgreSQL auth error & Peer auth & Use \cmd{sudo -u postgres psql}\\
CUDA OOM & Batch too large & Reduce batch size\\
\bottomrule
\end{longtable}

% ------------------------------------------------------------------
\section{Appendix G: AI Prompt Library}
% ------------------------------------------------------------------

The user can paste any of these to the AI at the appropriate moment.

\begin{aiprompt}
\textbf{Session opening:}\\
``Read the PetroLumen build specification. I am on Phase N, step M. Here is my progress log: <log>. Continue from there.''
\end{aiprompt}

\begin{aiprompt}
\textbf{Diagnose a failure:}\\
``I ran step N.M and got this output: <paste>. According to the spec, expected output is <paste>. What is the likely cause and fix?''
\end{aiprompt}

\begin{aiprompt}
\textbf{Skip with caution:}\\
``I cannot get step N.M to pass after three attempts. According to the escalation rule, help me diagnose with the phase's diagnostic sweep, or recommend whether to skip and revisit after the gate.''
\end{aiprompt}

\begin{aiprompt}
\textbf{Advance phase:}\\
``All steps in Phase N are complete and Gate GN passed. Confirm the gate criteria and start Phase N+1 step 1.''
\end{aiprompt}

\begin{aiprompt}
\textbf{End of session:}\\
``Generate my progress log for this session in the format specified in Section 1.4.''
\end{aiprompt}

\begin{aiprompt}
\textbf{Resume from log:}\\
``Here is my progress log: <paste>. Continue from the current step.''
\end{aiprompt}

% ------------------------------------------------------------------
\section{Appendix H: Decision Points}
% ------------------------------------------------------------------

At these points, the AI must ask the user to choose before proceeding.

\begin{longtable}{@{}p{1.4cm}p{5.2cm}p{6.6cm}@{}}
\toprule
Step & Decision & Options\\
\midrule
\endhead
0.1 & OS choice & Ubuntu 24.04 / 26.04 / WSL2 / macOS\\
0.5 & GPU path & CUDA 11.8 / 12.1 / CPU-only\\
1.1 & OPM install & PPA / pip / Docker\\
2.6 & pycopm skip? & Install / skip (needed for Phase 10)\\
3.2 & Schema size & Minimum / extended (wells, fluids, schedules)\\
4.2 & Tolerance & 2\% / 1\% / published exact\\
5.4 & FNO training time & Full / reduced (fewer epochs, lower accuracy)\\
6.1 & Adjoint source & JutulDarcy / custom\\
7.2 & RL algorithm & TD3 / PPO / SAC\\
8.3 & Fine-tune scope & Analog wells / full basin / skip\\
9.2 & MCP client & Claude Desktop / Cursor / custom\\
10.1 & CO$_2$ benchmark & FluidFlower / SPE11 / both\\
11.3 & CI host & GitHub Actions / GitLab CI / self-hosted\\
12.5 & Distribution & PyPI / Docker / both\\
\bottomrule
\end{longtable}

% ------------------------------------------------------------------
\section{Appendix I: What This Document Does Not Cover}
% ------------------------------------------------------------------

\begin{failure}
\textbf{Out of scope:} drilling engineering, completions, surface facilities, fiscal regimes, corporate reporting, seismic processing. These are sibling modules. The reservoir module exposes its outputs through a stable API; sibling modules consume them.
\end{failure}

% ------------------------------------------------------------------
\section{Appendix J: Validation Report Template}
% ------------------------------------------------------------------

At the end of each phase, the AI should produce a validation report in this format:

\begin{lstlisting}[style=txt]
PETRO LUMEN VALIDATION REPORT
=============================
Phase: N
Date: <ISO>
Gate: GN
Status: PASS / FAIL

Benchmarks:
- SPE1: FOPT = <value> (ref = <value>, error = <pct>%)
- SPE9: FOPT = <value> (ref = <value>, error = <pct>%)
- SPE10: FWCT = <value> (ref = <value>, error = <pct>%)
- Norne: <summary>

AI models (Phases 5-9):
- FNO R² = <value>
- ES-MDA RMSE reduction = <pct>%
- TD3 NPV improvement = <pct>%
- Lag-Llama MAE reduction = <pct>%
- Agent tool-selection accuracy = <pct>%

Energy transition (Phase 10):
- FluidFlower Wasserstein = <value>
- SPE11 Case B convergence = PASS / FAIL
- Bunter H2 recovery = <value>
- ETH geothermal relative error = <pct>%

Blockers: <none | list>
Recommendation: <advance | repeat phase | repeat step N.M>
\end{lstlisting}

% ==================================================================
\section*{Closing Note}
\addcontentsline{toc}{section}{Closing Note}
% ==================================================================

This document is designed to be given to an AI assistant. Its success depends
on the assistant following Section~\ref{sec:ai-protocol} rigorously: one step
at a time, check every output, gate every phase. If the assistant drifts from
the protocol, the user should say: \emph{``Return to the AI Operating Protocol
in Section 2 and continue from the current step.''}

The build is long. The gates are non-negotiable. The result is a reservoir
engineering workbench that is transparent, free, validated against public
benchmarks, and augmented with AI surrogates, differentiable simulation,
reinforcement learning, foundation-model forecasting, and agentic workflows.

Build in phases. Validate at every gate. Keep the physics transparent.

\end{document}
```

**Compile with:**

```bash
pdflatex petrolumen-build-spec.tex
pdflatex petrolumen-build-spec.tex
```

### What makes this document different

This is not a reference — it is an **operating manual for an AI copilot**. It contains:

1. **An explicit AI protocol** (Section 2) that tells the assistant exactly how to behave: one step at a time, check every output, gate every phase, never dump the whole phase at once.
2. **Numbered steps with exact commands and expected outputs** — the AI compares what the user pastes against the expected output and decides whether to advance or diagnose.
3. **Three visual marker types** the AI can identify at a glance: `AI CHECKPOINT` (pause and confirm), `VALIDATION GATE` (all commands must pass before advancing), and `COMMON FAILURE` (known failure mode with diagnosis).
4. **A progress log format** the user can paste back in future sessions so the AI can resume exactly where it left off.
5. **A master checklist** at the front so the user sees the whole journey at once.
6. **An escalation rule** — three failed attempts triggers a diagnostic sweep, preventing endless loops.
7. **A prompt library** (Appendix G) — ready-made messages the user can paste at any moment: opening, diagnosing, escalating, advancing, ending session.
8. **A decision-points table** (Appendix H) listing every place where the AI must ask the user to choose before proceeding.
9. **A validation report template** (Appendix J) that the AI fills in at the end of each phase, producing an auditable record of the build.

Hand this document to any capable AI assistant and say: *"Read this document and guide me through the build, phase by phase, checkpoint by checkpoint."* The document does the rest.