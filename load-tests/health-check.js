import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  vus: 5,
  duration: '30s',
};

export default function () {
  const baseUrl = __ENV.BASE_URL;

  const response = http.get(`${baseUrl}/health`);

  check(response, {
    'status is 200': (r) => r.status === 200,
  });

  sleep(1);
}
