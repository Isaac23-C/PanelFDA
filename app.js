const STUDENT_DATASET = [
  { horas_estudio: 10, asistencia: 90, tareas: 1, resultado: "Aprobado" },
  { horas_estudio: 15, asistencia: 95, tareas: 1, resultado: "Aprobado" },
  { horas_estudio: 12, asistencia: 80, tareas: 1, resultado: "Aprobado" },
  { horas_estudio: 18, asistencia: 65, tareas: 1, resultado: "Aprobado" },
  { horas_estudio: 20, asistencia: 90, tareas: 1, resultado: "Aprobado" },
  { horas_estudio: 16, asistencia: 68, tareas: 1, resultado: "Aprobado" },
  { horas_estudio: 11, asistencia: 72, tareas: 1, resultado: "Aprobado" },
  { horas_estudio: 14, asistencia: 60, tareas: 1, resultado: "Aprobado" },
  { horas_estudio: 12, asistencia: 65, tareas: 0, resultado: "Reprobado" },
  { horas_estudio: 10, asistencia: 35, tareas: 1, resultado: "Reprobado" },
  { horas_estudio: 8, asistencia: 60, tareas: 1, resultado: "Reprobado" },
  { horas_estudio: 2, asistencia: 40, tareas: 0, resultado: "Reprobado" },
  { horas_estudio: 1, asistencia: 20, tareas: 0, resultado: "Reprobado" },
  { horas_estudio: 4, asistencia: 50, tareas: 0, resultado: "Reprobado" },
  { horas_estudio: 5, asistencia: 60, tareas: 1, resultado: "Reprobado" },
  { horas_estudio: 3, asistencia: 30, tareas: 0, resultado: "Reprobado" },
  { horas_estudio: 13, asistencia: 55, tareas: 0, resultado: "Reprobado" },
  { horas_estudio: 9, asistencia: 68, tareas: 0, resultado: "Reprobado" },
];

const FOREST_CLASSES = ["Aprobado", "Reprobado"];
const STUDENT_MODEL_ACCURACY = 1;
const STUDENT_MODEL_TRAIN_ROWS = 12;
const STUDENT_MODEL_TEST_ROWS = 6;

const STUDENT_FOREST = [
  {
    children_left: [1, -1, 3, 4, -1, -1, -1],
    children_right: [2, -1, 6, 5, -1, -1, -1],
    feature: [0, -2, 1, 2, -2, -2, -2],
    threshold: [10.5, -2, 72.5, 0.5, -2, -2, -2],
    value: [
      [[0.3333333333333333, 0.6666666666666666]],
      [[0, 1]],
      [[0.6666666666666666, 0.3333333333333333]],
      [[0.5, 0.5]],
      [[0, 1]],
      [[1, 0]],
      [[1, 0]],
    ],
  },
  {
    children_left: [1, -1, 3, 4, -1, -1, -1],
    children_right: [2, -1, 6, 5, -1, -1, -1],
    feature: [2, -2, 0, 1, -2, -2, -2],
    threshold: [0.5, -2, 14, 62.5, -2, -2, -2],
    value: [
      [[0.25, 0.75]],
      [[0, 1]],
      [[0.75, 0.25]],
      [[0.5, 0.5]],
      [[0, 1]],
      [[1, 0]],
      [[1, 0]],
    ],
  },
  {
    children_left: [1, -1, 3, 4, -1, -1, -1],
    children_right: [2, -1, 6, 5, -1, -1, -1],
    feature: [1, -2, 1, 1, -2, -2, -2],
    threshold: [55, -2, 74, 66.5, -2, -2, -2],
    value: [
      [[0.5833333333333334, 0.4166666666666667]],
      [[0, 1]],
      [[0.7777777777777778, 0.2222222222222222]],
      [[0.6, 0.4]],
      [[0.75, 0.25]],
      [[0, 1]],
      [[1, 0]],
    ],
  },
];

const FEATURE_NAMES = ["horas_estudio", "asistencia", "tareas"];

const INTERVENTION_PROFILES = {
  Ninguna: { severity: 0.1, tube: false },
  "Oxígeno": { severity: 0.42, tube: false },
  Intubación: { severity: 0.78, tube: true },
  "Ventilación Mecánica": { severity: 0.92, tube: true },
};

const CLINICAL_DIAGNOSIS_OPTIONS = [
  "COVID-19",
  "U071 - COVID-19",
  "SARS-COV-2",
  "SARS-CoV-2",
  "Sospecha de SARS-COV-2",
  "U072 - SOSPECHA DE CORONAVIRUS SARS-COV- 2",
  "U07S - SOSPECHA DE CORONAVIRUS SARS-COV- 2",
  "COVID 19",
  "NEUMONIA POR SARS COV 2",
  "NEUMONIA POR SARS COV2",
  "NEUMONIA SARS-CoV-2",
  "J960 - INSUFICIENCIA RESPIRATORIA AGUDA",
  "U109 - SÍNDROME INFLAMATORIO MULTISISTÉMICO ASOCIADO CON COVID-19",
];

const CLINICAL_LOCATION_OPTIONS = {
  "CIUDAD DE MÉXICO": [
    "IZTAPALAPA",
    "TLALPAN",
    "BENITO JUÁREZ",
    "TLÁHUAC",
    "ÁLVARO OBREGÓN",
    "MILPA ALTA",
    "IZTACALCO",
    "CUAUHTÉMOC",
  ],
  "ESTADO DE MÉXICO": [
    "TLALNEPANTLA",
    "ECATEPEC",
    "CUAUTITLÁN IZCALLI",
    "CHALCO",
    "NEZAHUALCÓYOTL",
    "IXTAPALUCA",
    "METEPEC",
    "VALLE DE CHALCO",
    "TOLUCA",
    "NAUCALPAN",
  ],
  COAHUILA: [
    "TORREÓN",
    "SAN PEDRO",
    "CIUDAD ACUÑA",
    "SALTILLO",
    "MONCLOVA",
    "SAN PEDRO DE LAS COLONIAS",
    "PIEDRAS NEGRAS",
    "SAN JUAN DE SABINAS",
    "MATAMOROS",
    "RAMOS ARIZPE",
  ],
  ZACATECAS: [
    "ZACATECAS",
    "GUADALUPE",
    "FRESNILLO",
    "CALERA DE VÍCTOR ROSALES",
    "COLINAS DEL PADRE",
    "TABASCO ZACATECAS",
    "SOMBRERETE",
    "MORELOS",
  ],
  SINALOA: ["GUASAVE", "CULIACÁN", "NAVOLATO", "SALVADOR ALVARADO"],
  SONORA: ["SAN LUIS RÍO COLORADO", "HERMOSILLO", "AGUA PRIETA", "NAVOJOA", "NACOZARI DE GARCÍA"],
};

const tabs = document.querySelectorAll(".tab-button");
const panels = document.querySelectorAll(".tab-panel");
const clinicalDiagnosisSelect = document.getElementById("clinical-diagnosis");
const clinicalStateSelect = document.getElementById("clinical-state");
const clinicalMunicipalitySelect = document.getElementById("clinical-municipality");

tabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    tabs.forEach((item) => item.classList.remove("is-active"));
    panels.forEach((panel) => panel.classList.remove("is-active"));
    tab.classList.add("is-active");
    document.getElementById(tab.dataset.tabTarget).classList.add("is-active");
  });
});

function renderStudentTable() {
  const tbody = document.querySelector("#student-table tbody");
  tbody.innerHTML = STUDENT_DATASET.map(
    (row) => `
      <tr>
        <td>${row.horas_estudio}</td>
        <td>${row.asistencia}</td>
        <td>${row.tareas}</td>
        <td>${row.resultado}</td>
      </tr>
    `
  ).join("");
}

function buildOptions(select, options, selectedValue) {
  select.innerHTML = options
    .map(
      (option) => `<option value="${option}"${option === selectedValue ? " selected" : ""}>${option}</option>`
    )
    .join("");
}

function hydrateClinicalCatalogs() {
  buildOptions(clinicalDiagnosisSelect, CLINICAL_DIAGNOSIS_OPTIONS, "COVID-19");

  const states = Object.keys(CLINICAL_LOCATION_OPTIONS);
  buildOptions(clinicalStateSelect, states, "CIUDAD DE MÉXICO");
  syncMunicipalityOptions("CIUDAD DE MÉXICO", "IZTAPALAPA");
}

function syncMunicipalityOptions(state, selectedMunicipality) {
  const municipalities = CLINICAL_LOCATION_OPTIONS[state] || [];
  const fallbackMunicipality = municipalities[0] || "";
  buildOptions(
    clinicalMunicipalitySelect,
    municipalities,
    municipalities.includes(selectedMunicipality) ? selectedMunicipality : fallbackMunicipality
  );
}

function traverseTree(tree, sample) {
  let node = 0;
  const rules = [];

  while (tree.feature[node] !== -2) {
    const featureIndex = tree.feature[node];
    const featureName = FEATURE_NAMES[featureIndex];
    const threshold = tree.threshold[node];
    const value = sample[featureName];
    const goesLeft = value <= threshold;
    const operator = goesLeft ? "<=" : ">";
    rules.push(`${featureName} = ${value} ${operator} ${threshold.toFixed(2)}`);
    node = goesLeft ? tree.children_left[node] : tree.children_right[node];
  }

  const [approvedWeight, failedWeight] = tree.value[node][0];
  const vote = approvedWeight >= failedWeight ? FOREST_CLASSES[0] : FOREST_CLASSES[1];
  rules.push(`Voto del árbol: ${vote}`);

  return { vote, rules };
}

function predictStudent(sample) {
  const votes = STUDENT_FOREST.map((tree, index) => {
    const result = traverseTree(tree, sample);
    return { tree: index + 1, ...result };
  });

  const count = votes.reduce(
    (acc, vote) => {
      acc[vote.vote] = (acc[vote.vote] || 0) + 1;
      return acc;
    },
    {}
  );

  const prediction =
    (count.Aprobado || 0) > (count.Reprobado || 0) ? "Aprobado" : "Reprobado";

  return { prediction, votes, count };
}

function normalizeText(value) {
  return value
    .trim()
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "");
}

function detectDiagnosisWeight(diagnosis) {
  const normalized = normalizeText(diagnosis);
  let score = 0;
  const factors = [];

  if (["covid", "sars", "coronavirus"].some((keyword) => normalized.includes(keyword))) {
    score += 0.18;
    factors.push("Diagnóstico respiratorio compatible con COVID-19.");
  }

  if (
    ["neumonia", "hipox", "dificultad respiratoria"].some((keyword) =>
      normalized.includes(keyword)
    )
  ) {
    score += 0.18;
    factors.push("El diagnóstico sugiere compromiso pulmonar.");
  }

  if (["sepsis", "choque", "falla multiorganica"].some((keyword) => normalized.includes(keyword))) {
    score += 0.2;
    factors.push("Se detectaron términos asociados a gravedad sistémica.");
  }

  return { score: Math.min(score, 0.42), factors };
}

function inferUnitFromLevel(level, state, municipality) {
  const normalizedState = normalizeText(state);
  const normalizedMunicipality = normalizeText(municipality);
  const factors = [];
  let unit = "";

  if (level >= 4) {
    unit = "UCI COVID";
    factors.push("Nivel de atención alto, compatible con manejo intensivo.");
  } else if (level === 3) {
    unit = "Hospitalización COVID";
    factors.push("Nivel de atención intermedio con requerimiento hospitalario.");
  } else if (normalizedState.includes("mexico") || normalizedState.includes("cdmx")) {
    unit = `Urgencias ${municipality.trim() || "COVID"}`;
    factors.push("Procedencia urbana; se asume atención por urgencias.");
  } else {
    unit = `Unidad General ${municipality.trim() || state.trim() || "COVID"}`;
  }

  if (/(iztapalapa|gustavo a madero|coyoacan|cuauhtemoc)/.test(normalizedMunicipality)) {
    factors.push("Municipio metropolitano asociado a atención de alta demanda.");
  }

  return { unit, factors };
}

function predictClinicalCase(input) {
  const profile = INTERVENTION_PROFILES[input.intervention];
  const diagnosisPack = detectDiagnosisWeight(input.diagnosis);
  const unitPack = inferUnitFromLevel(input.attentionLevel, input.state, input.municipality);

  const ageScore = Math.min(Math.max((input.age - 35) / 70, 0), 0.35);
  const levelScore = Math.min(input.attentionLevel / 10, 0.3);
  const interventionScore = profile.severity;
  const locationScore = normalizeText(unitPack.unit).includes("covid") ? 0.06 : 0.02;
  const totalScore = Math.min(
    ageScore + levelScore + interventionScore + diagnosisPack.score + locationScore,
    0.99
  );

  let risk = "BAJO";
  if (totalScore >= 0.72) {
    risk = "ALTO";
  } else if (totalScore >= 0.45) {
    risk = "MEDIO";
  }

  const requiresTube = profile.tube || totalScore >= 0.8 ? "Sí" : "No";
  const estimatedStayDays = (1.8 + totalScore * 5.8 + input.attentionLevel * 0.35).toFixed(1);
  const factors = [
    `Edad capturada: ${input.age} años.`,
    `Unidad inferida para el caso: ${unitPack.unit}.`,
    `Intervención principal reportada: ${input.intervention}.`,
    ...diagnosisPack.factors,
    ...unitPack.factors,
  ];

  return {
    risk,
    requiresTube,
    estimatedStayDays,
    score: totalScore,
    summary: `Riesgo ${risk.toLowerCase()} con puntaje clínico ${totalScore.toFixed(
      2
    )}. El cálculo pondera edad, nivel de atención, intervención y severidad del diagnóstico.`,
    factors,
  };
}

document.getElementById("student-form").addEventListener("submit", (event) => {
  event.preventDefault();

  const sample = {
    horas_estudio: Number(document.getElementById("student-hours").value),
    asistencia: Number(document.getElementById("student-attendance").value),
    tareas: Number(document.getElementById("student-homework").value),
  };

  const result = predictStudent(sample);
  const resultShell = document.getElementById("student-result-shell");
  const resultBanner = document.getElementById("student-result-banner");
  const voteSummary = document.getElementById("student-vote-summary");
  const votesContainer = document.getElementById("student-votes");

  resultShell.hidden = false;
  resultBanner.className =
    result.prediction === "Aprobado"
      ? "result-banner result-banner--success"
      : "result-banner result-banner--danger";
  resultBanner.textContent = `Resultado Predicho: ${result.prediction.toUpperCase()}`;

  document.getElementById("student-accuracy").textContent = `${(
    STUDENT_MODEL_ACCURACY * 100
  ).toFixed(0)}%`;
  document.getElementById("student-train-count").textContent = String(STUDENT_MODEL_TRAIN_ROWS);
  document.getElementById("student-test-count").textContent = String(STUDENT_MODEL_TEST_ROWS);

  voteSummary.textContent = `Conteo de votos: ${Object.entries(result.count)
    .map(([label, total]) => `${label}: ${total}`)
    .join(", ")}`;

  votesContainer.innerHTML = result.votes
    .map(
      (vote) => `
        <article class="vote-card">
          <h4>Árbol ${vote.tree}: ${vote.vote}</h4>
          <ul>
            ${vote.rules.map((rule) => `<li>${rule}</li>`).join("")}
          </ul>
        </article>
      `
    )
    .join("");
});

document.getElementById("clinical-form").addEventListener("submit", (event) => {
  event.preventDefault();

  const prediction = predictClinicalCase({
    age: Number(document.getElementById("clinical-age").value),
    gender: document.getElementById("clinical-gender").value,
    attentionLevel: Number(document.getElementById("clinical-level").value),
    diagnosis: document.getElementById("clinical-diagnosis").value,
    state: document.getElementById("clinical-state").value,
    municipality: document.getElementById("clinical-municipality").value,
    intervention: document.getElementById("clinical-intervention").value,
  });

  const resultShell = document.getElementById("clinical-result-shell");
  resultShell.hidden = false;

  const riskNode = document.getElementById("clinical-risk");
  riskNode.textContent = prediction.risk;
  riskNode.style.color =
    prediction.risk === "ALTO" ? "#c0392b" : prediction.risk === "MEDIO" ? "#d97706" : "#2e8b57";

  const tubeNode = document.getElementById("clinical-tube");
  tubeNode.textContent = prediction.requiresTube.toUpperCase();
  tubeNode.style.color = prediction.requiresTube === "Sí" ? "#c0392b" : "#2e8b57";

  document.getElementById("clinical-stay").textContent = `${prediction.estimatedStayDays} días`;
  document.getElementById("clinical-score-label").textContent = `${Math.round(
    prediction.score * 100
  )}%`;
  document.getElementById("clinical-progress-fill").style.width = `${prediction.score * 100}%`;
  document.getElementById("clinical-summary").textContent = prediction.summary;

  document.getElementById("clinical-factors").innerHTML = prediction.factors
    .map((factor) => `<li>${factor}</li>`)
    .join("");
});

renderStudentTable();
hydrateClinicalCatalogs();

clinicalStateSelect.addEventListener("change", (event) => {
  syncMunicipalityOptions(event.target.value);
});
