<script>
	import { onMount } from 'svelte';
	import Globe3D from '$lib/components/Globe3D.svelte';
	import SatelliteTracker from '$lib/components/SatelliteTracker.svelte';
	import TelemetryPanel from '$lib/components/TelemetryPanel.svelte';
	import CoordinateSystemSelector from '$lib/components/CoordinateSystemSelector.svelte';
	import { satellites } from '$lib/stores/satellites';

	let backendStatus = 'Checking...';
	let apiConnected = false;
	let satelliteData = [];
	let loading = true;
	let errorMessage = '';

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
			const response = await fetch('http://localhost:8000/api/satellites?group=stations&limit=5');

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
				timestamp: sat.timestamp
			}));

			satellites.set(satelliteData);
			loading = false;

		} catch (error) {
			errorMessage = `Error loading satellites: ${error.message}`;
			loading = false;
			console.error('Error fetching satellites:', error);
		}
	}

	onMount(() => {
		checkBackend();
		fetchSatellites();

		const interval = setInterval(fetchSatellites, 30000);

		return () => clearInterval(interval);
	});
</script>

<div class="mission-control">
	<header class="header">
		<h1>Satellite Mission Control & Simulation System</h1>
		<div class="status" class:connected={apiConnected}>
			<span class="status-indicator"></span>
			<p>{backendStatus}</p>
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
					<Globe3D satellites={satelliteData} />
					<div class="sat-info">
						<p>{satelliteData.length} satellites tracked</p>
					</div>
				</div>
			{/if}
		</div>

		<div class="right-panel">
			<TelemetryPanel />
		</div>
	</main>
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

	.status {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
		font-size: 0.9rem;
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
</style>
