<script>
	import { onMount } from 'svelte';
	import Globe3D from '$lib/components/Globe3D.svelte';
	import SatelliteTracker from '$lib/components/SatelliteTracker.svelte';
	import TelemetryPanel from '$lib/components/TelemetryPanel.svelte';
	import CoordinateSystemSelector from '$lib/components/CoordinateSystemSelector.svelte';
	import GroundStationPanel from '$lib/components/GroundStationPanel.svelte';
	import { satellites, selectedSatellite } from '$lib/stores/satellites';

	let backendStatus = 'Checking...';
	let apiConnected = false;
	let satelliteData = [];
	let loading = true;
	let errorMessage = '';
	let selectedGroup = 'stations';
	let satelliteLimit = 20;
	let groundStations = []; // Array of ground stations
	let selectedGroundStation = null; // Currently selected ground station for topocentric
	let showPositionInput = false;
	let inputLat = '';
	let inputLon = '';
	let inputName = '';

	// Coordinate system state
	let coordinateSystem = 'ECI';

	const availableGroups = [
		{ id: 'stations', name: 'Space Stations', limit: 10 },
		{ id: 'starlink', name: 'Starlink', limit: 50 },
		{ id: 'weather', name: 'Weather Sats', limit: 20 },
		{ id: 'gps', name: 'GPS', limit: 30 }
	];

	async function checkBackend() {
		try {
			const response = await fetch('http://localhost:8000/health');
			const data = await response.json();
			backendStatus = `Backend: ${data.status}`;
			apiConnected = true;
		} catch (error) {
			backendStatus = 'Backend: Offline';
			apiConnected = false;
		}
	}

	async function fetchSatellites() {
		loading = true;
		errorMessage = '';

		try {
			const response = await fetch(`http://localhost:8000/api/satellites?group=${selectedGroup}&limit=${satelliteLimit}`);

			if (!response.ok) {
				throw new Error(`HTTP ${response.status}`);
			}

			const data = await response.json();

			satelliteData = data.satellites.map(sat => ({
				id: sat.id,
				name: sat.name,
				x: sat.position.x / 1000,
				y: sat.position.y / 1000,
				z: sat.position.z / 1000,
				vx: sat.velocity.vx,
				vy: sat.velocity.vy,
				vz: sat.velocity.vz,
				position: sat.position,
				velocity: sat.velocity,
				timestamp: sat.timestamp,
				tle: sat.tle
			}));

			satellites.set(satelliteData);
			loading = false;

		} catch (error) {
			errorMessage = `Error loading satellites: ${error.message}`;
			loading = false;
			console.error('Error fetching satellites:', error);
		}
	}

	function changeGroup(group) {
		selectedGroup = group.id;
		satelliteLimit = group.limit;
		selectedSatellite.set(null);
		fetchSatellites();
	}

	function addGroundStation() {
		const lat = parseFloat(inputLat);
		const lon = parseFloat(inputLon);

		if (isNaN(lat) || isNaN(lon) || lat < -90 || lat > 90 || lon < -180 || lon > 180) {
			alert('Please enter valid coordinates (Latitude: -90 to 90, Longitude: -180 to 180)');
			return;
		}

		const newStation = {
			id: Date.now(), // Unique ID
			lat: lat,
			lon: lon,
			name: inputName || `Station ${groundStations.length + 1}`
		};

		groundStations = [...groundStations, newStation];

		// Auto-select first ground station for topocentric
		if (groundStations.length === 1) {
			selectedGroundStation = newStation;
		}

		// Clear inputs
		inputLat = '';
		inputLon = '';
		inputName = '';
		showPositionInput = false;

		console.log('Ground station added:', newStation);
	}

	function removeGroundStation(stationId) {
		groundStations = groundStations.filter(s => s.id !== stationId);

		// If removed station was selected, select first available
		if (selectedGroundStation?.id === stationId) {
			selectedGroundStation = groundStations[0] || null;
		}
	}

	function selectGroundStation(station) {
		selectedGroundStation = station;
		console.log('Ground station selected:', station);
	}

	onMount(() => {
		checkBackend();
		fetchSatellites();

		// Update from backend every 15 seconds for accuracy
		const interval = setInterval(fetchSatellites, 15000);

		return () => clearInterval(interval);
	});
</script>

<div class="mission-control">
	<header class="header">
		<h1>Satellite Mission Control & Simulation System</h1>
		<div class="header-controls">
			<div class="status" class:connected={apiConnected}>
				<span class="status-indicator"></span>
				<p>{backendStatus}</p>
			</div>
			<div class="group-selector">
				{#each availableGroups as group}
					<button
						class="group-btn"
						class:active={selectedGroup === group.id}
						on:click={() => changeGroup(group)}
					>
						{group.name}
					</button>
				{/each}
			</div>
			<button class="position-btn" on:click={() => showPositionInput = !showPositionInput}>
				📍 Add Ground Station ({groundStations.length})
			</button>
		</div>
	</header>

	<main class="content">
		<div class="left-panel">
			<div class="panel-section">
				<SatelliteTracker />
			</div>
			<div class="panel-section">
				<CoordinateSystemSelector />
		</div>
		<div class="panel-section">
			<GroundStationPanel
				groundStations={groundStations}
				selectedGroundStation={selectedGroundStation}
				onSelect={selectGroundStation}
				onRemove={removeGroundStation}
			/>
			</div>
		</div>

		<div class="center-panel">
			{#if loading}
				<div class="loading-state">
					<div class="spinner"></div>
					<p>Loading satellite data from CelesTrak...</p>
				</div>
			{:else if errorMessage}
				<div class="error-state">
					<p>{errorMessage}</p>
					<button on:click={fetchSatellites}>Retry</button>
				</div>
			{:else}
				<div class="globe-wrapper">
					<Globe3D satellites={satelliteData} groundStations={groundStations} selectedGroundStation={selectedGroundStation} />
					<div class="sat-info">
						<p>{satelliteData.length} satellites tracked</p>
						<p class="user-pos-info">📍 {groundStations.length} ground stations</p>
					</div>
				</div>
			{/if}
		</div>

		<div class="right-panel">
			<TelemetryPanel />
		</div>
	</main>

	<!-- Position Input Modal -->
	{#if showPositionInput}
		<div class="modal-overlay" on:click={() => showPositionInput = false}>
			<div class="modal-content" on:click|stopPropagation>
				<h3>Set Your Position</h3>
				<div class="input-group">
					<label>
						Latitude (-90 to 90):
						<input type="number" bind:value={inputLat} placeholder="e.g., 40.7128" step="0.0001" min="-90" max="90" />
					</label>
					<label>
						Longitude (-180 to 180):
						<input type="number" bind:value={inputLon} placeholder="e.g., -74.0060" step="0.0001" min="-180" max="180" />
					</label>
					<label>
						Location Name (optional):
						<input type="text" bind:value={inputName} placeholder="e.g., New York City" />
					</label>
				</div>
				<div class="modal-actions">
					<button class="btn-primary" on:click={addGroundStation}>Add Station</button>
					<button class="btn-secondary" on:click={() => showPositionInput = false}>Cancel</button>
				</div>
			</div>
		</div>
	{/if}
</div>

<style>
	.mission-control {
		width: 100%;
		height: 100vh;
		display: flex;
		flex-direction: column;
		overflow: hidden;
	}

	.header {
		background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 100%);
		padding: 1rem 2rem;
		color: white;
		text-align: center;
		border-bottom: 2px solid #646cff;
		flex-shrink: 0;
	}

	.header h1 {
		margin: 0 0 0.5rem 0;
		font-size: 1.5rem;
		font-weight: 600;
	}

	.header-controls {
		display: flex;
		justify-content: space-between;
		align-items: center;
		gap: 2rem;
	}

	.status {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.9rem;
	}

	.group-selector {
		display: flex;
		gap: 0.5rem;
	}

	.group-btn {
		padding: 0.4rem 1rem;
		background: rgba(255, 255, 255, 0.1);
		border: 1px solid rgba(255, 255, 255, 0.2);
		border-radius: 6px;
		color: white;
		font-size: 0.85rem;
		cursor: pointer;
		transition: all 0.2s;
	}

	.group-btn:hover {
		background: rgba(255, 255, 255, 0.2);
		border-color: #646cff;
	}

	.group-btn.active {
		background: #646cff;
		border-color: #646cff;
		font-weight: 600;
	}

	.status-indicator {
		width: 10px;
		height: 10px;
		border-radius: 50%;
		background-color: #ef4444;
		animation: pulse 2s ease-in-out infinite;
	}

	.status.connected .status-indicator {
		background-color: #22c55e;
	}

	@keyframes pulse {
		0%, 100% { opacity: 1; }
		50% { opacity: 0.5; }
	}

	.content {
		flex: 1;
		display: grid;
		grid-template-columns: 300px 1fr 350px;
		gap: 1rem;
		padding: 1rem;
		overflow: hidden;
	}

	.left-panel,
	.right-panel {
		display: flex;
		flex-direction: column;
		gap: 1rem;
		overflow-y: auto;
	}

	.panel-section {
		flex-shrink: 0;
	}

	.center-panel {
		display: flex;
		flex-direction: column;
		min-height: 0;
		height: 100%;
		position: relative;
	}

	@media (max-width: 1200px) {
		.content {
			grid-template-columns: 1fr;
			grid-template-rows: auto 1fr auto;
		}

		.left-panel,
		.right-panel {
			flex-direction: row;
			overflow-x: auto;
		}
	}

	.loading-state,
	.error-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		height: 100%;
		color: rgba(255, 255, 255, 0.7);
	}

	.spinner {
		width: 50px;
		height: 50px;
		border: 4px solid rgba(100, 108, 255, 0.3);
		border-top-color: #646cff;
		border-radius: 50%;
		animation: spin 1s linear infinite;
		margin-bottom: 1rem;
	}

	@keyframes spin {
		to { transform: rotate(360deg); }
	}

	.error-state p {
		margin-bottom: 1rem;
		color: #ef4444;
	}

	.error-state button {
		padding: 0.6em 1.2em;
		background-color: #646cff;
		border: none;
		border-radius: 6px;
		color: white;
		cursor: pointer;
		font-weight: 500;
	}

	.error-state button:hover {
		background-color: #535bf2;
	}

	.globe-wrapper {
		width: 100%;
		height: 100%;
		position: relative;
	}

	.sat-info {
		position: absolute;
		bottom: 1rem;
		left: 1rem;
		background: rgba(0, 0, 0, 0.7);
		padding: 0.5rem 1rem;
		border-radius: 6px;
		color: #22c55e;
		font-size: 0.9rem;
		font-weight: 500;
		z-index: 10;
	}

	.sat-info p {
		margin: 0.25rem 0;
	}

	.user-pos-info {
		color: #00ffff !important;
		font-weight: 600;
	}

	.position-btn {
		padding: 0.4rem 1rem;
		background: rgba(0, 255, 255, 0.2);
		border: 1px solid #00ffff;
		border-radius: 6px;
		color: #00ffff;
		font-size: 0.85rem;
		cursor: pointer;
		transition: all 0.2s;
		font-weight: 500;
	}

	.position-btn:hover {
		background: rgba(0, 255, 255, 0.3);
		box-shadow: 0 0 10px rgba(0, 255, 255, 0.3);
	}

	.modal-overlay {
		position: fixed;
		top: 0;
		left: 0;
		right: 0;
		bottom: 0;
		background: rgba(0, 0, 0, 0.7);
		display: flex;
		align-items: center;
		justify-content: center;
		z-index: 1000;
		backdrop-filter: blur(4px);
	}

	.modal-content {
		background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 100%);
		border: 2px solid #646cff;
		border-radius: 12px;
		padding: 2rem;
		max-width: 500px;
		width: 90%;
		box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
	}

	.modal-content h3 {
		margin: 0 0 1.5rem 0;
		color: #00ffff;
		font-size: 1.3rem;
	}

	.input-group {
		display: flex;
		flex-direction: column;
		gap: 1rem;
		margin-bottom: 1.5rem;
	}

	.input-group label {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
		color: rgba(255, 255, 255, 0.9);
		font-size: 0.9rem;
	}

	.input-group input {
		padding: 0.6rem;
		background: rgba(255, 255, 255, 0.1);
		border: 1px solid rgba(255, 255, 255, 0.2);
		border-radius: 6px;
		color: white;
		font-size: 0.95rem;
	}

	.input-group input:focus {
		outline: none;
		border-color: #00ffff;
		box-shadow: 0 0 0 2px rgba(0, 255, 255, 0.2);
	}

	.modal-actions {
		display: flex;
		gap: 0.5rem;
		justify-content: flex-end;
	}

	.btn-primary,
	.btn-secondary {
		padding: 0.6rem 1.2rem;
		border: none;
		border-radius: 6px;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s;
	}

	.btn-primary {
		background: #00ffff;
		color: #0a0e27;
	}

	.btn-primary:hover {
		background: #00cccc;
		box-shadow: 0 0 15px rgba(0, 255, 255, 0.5);
	}

	.btn-secondary {
		background: rgba(255, 255, 255, 0.1);
		color: white;
		border: 1px solid rgba(255, 255, 255, 0.2);
	}

	.btn-secondary:hover {
		background: rgba(255, 255, 255, 0.2);
	}
</style>
