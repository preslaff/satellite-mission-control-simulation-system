<script>
	import { onMount } from 'svelte';
	import Globe3D from '$lib/components/Globe3D.svelte';
	import SatelliteTracker from '$lib/components/SatelliteTracker.svelte';
	import TelemetryPanel from '$lib/components/TelemetryPanel.svelte';
	import CoordinateSystemSelector from '$lib/components/CoordinateSystemSelector.svelte';

	let backendStatus = 'Checking...';
	let apiConnected = false;

	let testSatellites = [
		{ id: 1, name: 'ISS', x: 8, y: 2, z: 5 },
		{ id: 2, name: 'Hubble', x: -7, y: 4, z: -3 },
		{ id: 3, name: 'Starlink-1234', x: 5, y: 6, z: 8 }
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

	onMount(() => {
		checkBackend();
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
			<Globe3D satellites={testSatellites} />
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
</style>
