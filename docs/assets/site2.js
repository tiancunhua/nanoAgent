document.addEventListener("DOMContentLoaded", () => {
  const randomButton = document.querySelector("[data-random-question]");
  const randomOutput = document.querySelector(".random-question");
  const questions = [
    "“你们安装过哪些 Agent？OpenClaw、Claude Code，还是 Codex？”",
    "“如果 AI 能替你完成一件重复工作，你会选什么？”",
    "“AI 给出建议，和 AI 完成任务，区别在哪里？”",
    "“你会放心让 Agent 直接发布代码吗？为什么？”",
  ];
  let questionIndex = 0;

  randomButton?.addEventListener("click", () => {
    questionIndex = (questionIndex + 1) % questions.length;
    randomOutput.classList.remove("is-changing");
    void randomOutput.offsetWidth;
    randomOutput.classList.add("is-changing");
    randomOutput.textContent = questions[questionIndex];
  });

  const runButton = document.querySelector("[data-run-loop]");
  const resetButton = document.querySelector("[data-reset-loop]");
  const loopSteps = [...document.querySelectorAll("[data-loop-step]")];
  const loopLog = document.querySelector("[data-loop-log]");
  const loopDecision = document.querySelector("[data-loop-decision]");
  const loopDetails = [...document.querySelectorAll("[data-loop-detail]")];
  const loopRound = document.querySelector("[data-loop-round]");
  const logLines = [
    '<span class="terminal-blue">[think]</span> 我需要先找到所有 TODO 标记。',
    '<span class="terminal-coral">[tool]</span> search_files({ query: "TODO" })',
    '<span class="terminal-lime">[result]</span> 找到 6 条结果，分布在 4 个文件。',
    '<span class="terminal-blue">[loop]</span> 还没完成。带着搜索结果重新思考。',
    '<span class="terminal-blue">[think]</span> 信息足够。现在按文件和优先级整理。',
    '<span class="terminal-coral">[tool]</span> write_file({ path: "todo-report.md" })',
    '<span class="terminal-lime">[done]</span> 清单已生成：todo-report.md',
  ];
  const loopFrames = [
    { step: 0, logCount: 1, round: "first", details: ["先搜索项目里的 TODO", "调用文件搜索工具", "等待读取结果"] },
    { step: 1, logCount: 2, round: "first" },
    { step: 2, logCount: 3, round: "first" },
    { step: null, decision: "return", logCount: 4, round: "return" },
    { step: 0, revisit: true, logCount: 5, round: "second", details: ["根据搜索结果制定整理方案", "写入清单文件", "检查写入结果"] },
    { step: 1, logCount: 6, round: "second" },
    { step: 2, logCount: 6, round: "second" },
    { step: null, decision: "complete", logCount: 7, round: "second" },
    { step: 3, decision: "complete", logCount: 7, round: "done" },
  ];
  let loopTimer = null;
  let loopFrameIndex = -1;

  function resetLoop() {
    window.clearInterval(loopTimer);
    loopTimer = null;
    loopFrameIndex = -1;
    runButton.disabled = false;
    runButton.innerHTML = "运行 Agent <span>▶</span>";
    loopSteps.forEach((step, index) => {
      step.classList.remove("is-active", "is-done", "is-revisited");
      step.classList.toggle("is-ready", index === 0);
    });
    loopDecision?.classList.remove("is-active", "is-returning", "is-complete");
    if (loopRound) {
      loopRound.className = "loop-round";
      loopRound.innerHTML = "<span>第 1 轮</span> 从目标出发";
    }
    const initialDetails = ["先搜索项目里的 TODO", "调用文件搜索工具", "读到 6 条搜索结果"];
    loopDetails.forEach((detail, index) => {
      detail.textContent = initialDetails[index];
    });
    loopLog.innerHTML = '<span class="terminal-muted">$ 等待运行…</span>';
  }

  function renderLoopFrame() {
    const frame = loopFrames[loopFrameIndex];
    loopSteps.forEach((step, index) => {
      step.classList.toggle("is-active", index === frame.step);
      step.classList.toggle("is-revisited", Boolean(index === frame.step && frame.revisit));
      step.classList.toggle("is-done", frame.step === 3 && index < 3);
      step.classList.remove("is-ready");
    });
    loopDecision?.classList.toggle("is-active", Boolean(frame.decision));
    loopDecision?.classList.toggle("is-returning", frame.decision === "return");
    loopDecision?.classList.toggle("is-complete", frame.decision === "complete");
    if (loopRound) {
      const roundCopy = {
        first: "<span>第 1 轮</span> 先寻找信息",
        return: "<span>未完成</span> ↺ 回到思考",
        second: "<span>第 2 轮</span> 带着结果继续",
        done: "<span>完成</span> 输出最终结果",
      };
      loopRound.innerHTML = roundCopy[frame.round];
      loopRound.classList.toggle("is-returning", frame.round === "return");
      loopRound.classList.toggle("is-second", frame.round === "second");
    }

    if (frame.details) {
      loopDetails.forEach((detail, index) => {
        detail.textContent = frame.details[index];
      });
    }
    loopLog.innerHTML = logLines.slice(0, frame.logCount).join("\n");

    if (loopFrameIndex >= loopFrames.length - 1) {
      window.clearInterval(loopTimer);
      loopTimer = null;
      runButton.disabled = false;
      runButton.innerHTML = "再运行一次 <span>↻</span>";
    }
  }

  runButton?.addEventListener("click", () => {
    resetLoop();
    runButton.disabled = true;
    runButton.textContent = "Agent 运行中…";
    loopFrameIndex = 0;
    renderLoopFrame();
    loopTimer = window.setInterval(() => {
      loopFrameIndex += 1;
      renderLoopFrame();
    }, 1000);
  });

  resetButton?.addEventListener("click", resetLoop);

  const skillTabs = [...document.querySelectorAll("[data-skill-tab]")];
  const skillNotes = {
    trigger: {
      title: "触发器要具体。",
      body: "写出任务类型和用户常用说法，让 Agent 知道什么时候应该加载这份手册。",
    },
    steps: {
      title: "步骤要能直接执行。",
      body: "写清顺序、工具和检查点。避免“适当处理”“自行判断”这类模糊动作。",
    },
    guardrail: {
      title: "把容易走错的岔路口堵上。",
      body: "告诉 Agent 何时停止、何时询问、什么绝对不能做。",
    },
    output: {
      title: "先定义完成的样子。",
      body: "明确文件、格式、位置和验收标准，Agent 才知道什么时候真的做完了。",
    },
  };
  const skillNote = document.querySelector("[data-skill-note]");
  const codeParts = [...document.querySelectorAll("[data-code-part]")];

  function activateSkillTab(name) {
    skillTabs.forEach((tab) => {
      const active = tab.dataset.skillTab === name;
      tab.classList.toggle("is-active", active);
      tab.setAttribute("aria-selected", String(active));
    });
    codeParts.forEach((part) => {
      part.classList.toggle("is-active", part.dataset.codePart === name);
    });
    skillNote.innerHTML = `<strong>${skillNotes[name].title}</strong><p>${skillNotes[name].body}</p>`;
  }

  skillTabs.forEach((tab) => {
    tab.addEventListener("click", () => activateSkillTab(tab.dataset.skillTab));
  });

  activateSkillTab("trigger");
});
