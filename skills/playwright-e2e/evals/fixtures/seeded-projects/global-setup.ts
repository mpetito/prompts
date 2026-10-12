import { request, type FullConfig } from '@playwright/test';

// Resets the test database once per run, seeds one user with two projects,
// and saves that user's signed-in state for every test.
export default async function globalSetup(config: FullConfig) {
  const baseURL = config.projects[0].use.baseURL!;
  const api = await request.newContext({ baseURL });
  await api.post('/test-api/reset');
  await api.post('/test-api/users', { data: { email: 'demo@example.test', password: 'demo-pass' } });
  for (const name of ['Acme Launch', 'Beta Site']) {
    await api.post('/test-api/projects', { data: { owner: 'demo@example.test', name } });
  }
  await api.post('/api/login', { data: { email: 'demo@example.test', password: 'demo-pass' } });
  await api.storageState({ path: '.auth/demo.json' });
  await api.dispose();
}
