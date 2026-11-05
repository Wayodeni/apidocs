const failureThreshold = 5;
const maxResponseSize = 64 * 1024;

function checkBlock(request) {
    if (request.method !== 'POST') {
        return;
    }

    const remaining = ngx.shared.login_blocks.ttl(request.remoteAddress);
    if (remaining > 0) {
        request.headersOut['Retry-After'] = String(Math.ceil(remaining / 1000));
        request.headersOut['Cache-Control'] = 'no-store';
        request.return(429, 'Too many login attempts. Try again later.\n');
    }
}

function resetOnSuccess(request) {
    if (request.method === 'POST' && request.status === 200) {
        ngx.shared.login_windows.delete(request.remoteAddress);
    }
}

function inspectResponse(request, data, flags) {
    if (request.method !== 'POST' || request.status !== 500) {
        request.sendBuffer(data, flags);
        request.done();
        return;
    }

    const body = request.variables.login_response_body + data.toString('utf8');
    if (body.length > maxResponseSize) {
        request.done();
    } else if (flags.last) {
        recordFailure(request, body);
    } else {
        request.variables.login_response_body = body;
    }

    request.sendBuffer(data, flags);
}

function recordFailure(request, body) {
    let response;
    try {
        response = JSON.parse(body);
    } catch {
        return;
    }

    if (response?.message !== 'Unauthorized') {
        return;
    }

    const ip = request.remoteAddress;
    const windows = ngx.shared.login_windows;
    windows.add(ip, request.variables.request_id);
    const window = windows.get(ip);
    if (window === undefined) {
        return;
    }

    // A new window gets its own counter even while an expired entry remains in memory.
    const failures = ngx.shared.login_failures.incr(window, 1);
    if (failures >= failureThreshold && windows.get(ip) === window &&
        ngx.shared.login_blocks.add(ip, 1)) {
        const remaining = ngx.shared.login_blocks.ttl(ip);
        request.variables.login_blocked_until = new Date(Date.now() + remaining).toISOString();
    }
}

export default { checkBlock, resetOnSuccess, inspectResponse };
