// ============================================================
// Bolão Copa 2026 — Classificação de grupos (FIFA Art. 13)
// ============================================================
// Inicializado automaticamente via GROUPS_DATA injetado pelo
// servidor. Renderiza as tabelas de classificação de cada grupo.
// ============================================================

// ── Cálculo ─────────────────────────────────────────────────

function computeTeamStats(teamId, matches) {
  const finished = matches.filter(
    m => m.is_finished &&
         m.home_score != null &&
         m.away_score != null &&
         (m.home_team_id === teamId || m.away_team_id === teamId)
  );

  let played = 0, won = 0, drawn = 0, lost = 0, goalsFor = 0, goalsAgainst = 0;

  finished.forEach(m => {
    played++;
    const isHome = m.home_team_id === teamId;
    const teamScore = isHome ? m.home_score : m.away_score;
    const oppScore  = isHome ? m.away_score : m.home_score;
    goalsFor     += teamScore;
    goalsAgainst += oppScore;
    if (teamScore > oppScore)      won++;
    else if (teamScore < oppScore) lost++;
    else                           drawn++;
  });

  return {
    played, won, drawn, lost, goalsFor, goalsAgainst,
    goalDiff: goalsFor - goalsAgainst,
    points: won * 3 + drawn,
  };
}

// Pontos → saldo → gols marcados. Retorna 0 se igual nos três.
function compareStats(a, b) {
  if (b.points   !== a.points)   return b.points   - a.points;
  if (b.goalDiff !== a.goalDiff) return b.goalDiff - a.goalDiff;
  if (b.goalsFor !== a.goalsFor) return b.goalsFor - a.goalsFor;
  return 0;
}

// Fallback final: saldo geral → gols gerais → alfabético.
function fallbackByOverallStats(tiedTeams) {
  return [...tiedTeams].sort((a, b) => {
    if (b.goalDiff !== a.goalDiff) return b.goalDiff - a.goalDiff;
    if (b.goalsFor !== a.goalsFor) return b.goalsFor - a.goalsFor;
    return a.team.name.localeCompare(b.team.name);
  });
}

// Resolve empatados em pontos via H2H (FIFA Art. 13 — Passos 1 e 2).
function resolveTiedGroup(tiedTeams, allMatches) {
  if (tiedTeams.length === 1) return tiedTeams;

  const tiedIds = new Set(tiedTeams.map(t => t.team.id));
  const h2hMatches = allMatches.filter(
    m => m.is_finished &&
         m.home_score != null &&
         m.away_score != null &&
         tiedIds.has(m.home_team_id) &&
         tiedIds.has(m.away_team_id)
  );

  // Nenhum jogo H2H finalizado → fallback direto
  if (h2hMatches.length === 0) return fallbackByOverallStats(tiedTeams);

  const withH2H = tiedTeams.map(t => ({
    ...t,
    h2h: computeTeamStats(t.team.id, h2hMatches),
  }));
  withH2H.sort((a, b) => compareStats(a.h2h, b.h2h));

  const result = [];
  let i = 0;
  while (i < withH2H.length) {
    let j = i + 1;
    while (j < withH2H.length && compareStats(withH2H[j].h2h, withH2H[i].h2h) === 0) j++;

    if (j - i === 1) {
      result.push(withH2H[i]);
    } else if (j - i === tiedTeams.length) {
      // H2H não separou ninguém → fallback por stats gerais (evita loop infinito)
      result.push(...fallbackByOverallStats(tiedTeams));
    } else {
      // Subgrupo parcialmente empatado → reaplica H2H só entre eles (Passo 2)
      result.push(...resolveTiedGroup(withH2H.slice(i, j), allMatches));
    }
    i = j;
  }
  return result;
}

// Função principal: retorna array ordenado com stats completos.
function calculateStandings(teams, matches) {
  const withStats = teams.map(team => ({
    team,
    ...computeTeamStats(team.id, matches),
  }));

  withStats.sort((a, b) => b.points - a.points);

  const result = [];
  let i = 0;
  while (i < withStats.length) {
    let j = i + 1;
    while (j < withStats.length && withStats[j].points === withStats[i].points) j++;
    if (j - i === 1) result.push(withStats[i]);
    else             result.push(...resolveTiedGroup(withStats.slice(i, j), matches));
    i = j;
  }
  return result;
}

// ── Renderização ─────────────────────────────────────────────

function renderStandingsTable(container, standings) {
  const rows = standings.map((s, idx) => {
    const pos = idx + 1;
    const q   = pos <= 2;
    const sg  = s.goalDiff > 0 ? '+' + s.goalDiff : String(s.goalDiff);
    const sgCls = s.goalDiff > 0
      ? 'text-green-600 font-semibold'
      : s.goalDiff < 0 ? 'text-red-600' : 'text-gray-500';
    const posCls = pos === 1 ? 'text-green-600'
                 : pos === 2 ? 'text-green-500'
                 : 'text-gray-500';

    return `
      <tr class="${q ? 'bg-green-50' : ''}">
        <td class="pl-4 pr-2 py-2.5 text-sm font-black ${posCls}">${pos}</td>
        <td class="px-2 py-2.5">
          <div class="flex items-center gap-1.5">
            <span class="qual-bar ${q ? 'bg-green-400' : 'bg-gray-200'}"></span>
            <span class="text-lg leading-none">${s.team.flag}</span>
            <span class="font-semibold text-gray-800 text-sm">${s.team.name}</span>
          </div>
        </td>
        <td class="px-2 py-2.5 text-center text-sm text-gray-500">${s.played}</td>
        <td class="px-2 py-2.5 text-center text-sm text-gray-500">${s.won}</td>
        <td class="px-2 py-2.5 text-center text-sm text-gray-500">${s.drawn}</td>
        <td class="px-2 py-2.5 text-center text-sm text-gray-500">${s.lost}</td>
        <td class="px-2 py-2.5 text-center text-sm ${sgCls}">${sg}</td>
        <td class="pr-4 pl-2 py-2.5 text-center font-black text-gray-900 text-base">${s.points}</td>
      </tr>`;
  }).join('');

  container.innerHTML = `
    <table class="w-full">
      <thead>
        <tr class="text-sm text-gray-600 uppercase tracking-wide border-b border-gray-50">
          <th class="pl-4 pr-2 py-2 text-left w-6">#</th>
          <th class="px-2 py-2 text-left">Seleção</th>
          <th class="px-2 py-2 text-center">J</th>
          <th class="px-2 py-2 text-center">V</th>
          <th class="px-2 py-2 text-center">E</th>
          <th class="px-2 py-2 text-center">D</th>
          <th class="px-2 py-2 text-center">SG</th>
          <th class="pr-4 pl-2 py-2 text-center font-bold text-gray-600">P</th>
        </tr>
      </thead>
      <tbody class="divide-y divide-gray-50">${rows}</tbody>
    </table>
    <div class="px-4 py-2 bg-gray-50 border-t border-gray-100">
      <p class="text-sm text-gray-600 flex items-center gap-1.5">
        <span class="qual-bar bg-green-400"></span>
        Classificados para as oitavas de final
      </p>
    </div>`;
}

// ── Bootstrap ─────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', function () {
  if (typeof GROUPS_DATA === 'undefined') return;

  GROUPS_DATA.forEach(function (group) {
    const container = document.getElementById('standings-' + group.name);
    if (!container) return;
    const standings = calculateStandings(group.teams, group.matches);
    renderStandingsTable(container, standings);
  });
});
