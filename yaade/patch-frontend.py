from hashlib import sha256


def read(path):
    with open(path, 'rb') as file:
        return file.read()


def write(path, content):
    with open(path, 'wb') as file:
        file.write(content)


def replace_once(content, original, replacement):
    if content.count(original) != 1:
        raise SystemExit('Unexpected Yaade web assets. Review patch anchor: ' + repr(original))
    return content.replace(original, replacement, 1)


# Match the response parser and panel in the frontend shipped by the pinned image.
asset = b'assets/index.57773e9a.js'
bundle = read(asset)
bundle = replace_once(
    bundle,
    b'return{headers:t,body:n,status:e.status,time:e.time,size:o,date:l}',
    b'return{headers:t,body:n,rawBody:n===e.body?void 0:e.body,status:e.status,time:e.time,size:o,date:l}',
)

display_helper = br'''
function getResponseBodyDisplay(response, contentType, mode) {
    const body = response?.body ?? '';
    const rawBody = response?.rawBody ?? body;
    if (mode === 'plain') {
        return {body: rawBody, contentType: 'text/plain'};
    }

    const mediaType = contentType.split(';', 1)[0].trim().toLowerCase();
    if (mode === 'json' || mediaType === 'text/plain') {
        try {
            JSON.parse(rawBody);
            return {body: beautify_1(rawBody, {format: 'json'}), contentType: 'application/json'};
        } catch {
            return {body: rawBody, contentType: 'text/plain'};
        }
    }
    return {body, contentType};
}
'''
bundle = replace_once(
    bundle,
    b'function ResponsePanel({response:e}){var c,a,u;const{colorMode:t}=useColorMode(),s=useToast(),'
    b'{onCopy:n}=useClipboard((c=e==null?void 0:e.body)!=null?c:"");'
    b'function o(){n(),successToast("Copied to clipboard",s)}'
    b'const i=getContentType((a=e==null?void 0:e.headers)!=null?a:[]),l=getExtensions(i);',
    display_helper + b'''function ResponsePanel({response:e}) {
    var u;
    const {colorMode:t} = useColorMode(), s = useToast();
    const [mode, setMode] = react.exports.useState('auto');
    const contentType = getContentType(e?.headers ?? []);
    const display = react.exports.useMemo(() => getResponseBodyDisplay(e, contentType, mode),
        [e, contentType, mode]);
    const l = getExtensions(display.contentType);
    const {onCopy:n} = useClipboard(display.body);
    function o() {n(); successToast('Copied to clipboard', s);}
''',
)
bundle = replace_once(
    bundle,
    b'jsx(TabPanel,{children:jsx(ReactCodeMirror,{height:"100%",extensions:l,theme:t,value:e.body,editable:!1})})',
    b'''jsxs(TabPanel,{children:[
        jsxs(Select, {'aria-label':'Response body format', size:'xs', width:'auto', mb:2,
            value:mode, onChange:event => setMode(event.target.value), children:[
                jsx('option', {value:'auto', children:'Auto'}),
                jsx('option', {value:'json', children:'JSON'}),
                jsx('option', {value:'plain', children:'Plain'})
            ]}),
        jsx(ReactCodeMirror,{height:'100%',extensions:l,theme:t,value:display.body,editable:false})
    ]})''',
)

# Keep script headers scoped to one send and apply them after interpolation and built-in auth.
script_header_helpers = br'''
function setRequestScriptHeader(headers, name, value) {
    if (typeof name !== 'string' || !/^[!#$%&'*+.^_`|~0-9A-Za-z-]+$/.test(name)) {
        throw new Error('Invalid HTTP header name');
    }
    if (typeof value !== 'string' || /[\x00-\x08\x0a-\x1f\x7f]/.test(value)) {
        throw new Error('Invalid HTTP header value');
    }
    headers.set(name.toLowerCase(), {key: name, value, isEnabled: true});
}

function applyRequestScriptHeaders(request, headers) {
    if (!headers.size) return;
    request.data.headers = [
        ...(request.data.headers ?? []).filter(row => !headers.has(row.key.toLowerCase())),
        ...headers.values(),
    ];
}
'''
bundle = replace_once(
    bundle,
    b'async function executeRequestScript(e,t,s,n,o,i,l){',
    script_header_helpers + b'async function executeRequestScript(e,t,s,n,o,i,l,scriptHeaders){',
)
bundle = replace_once(
    bundle,
    b'headers:kvRowsToMap((a=e.data.headers)!=null?a:[])},c.jp=jpath',
    b'headers:kvRowsToMap((a=e.data.headers)!=null?a:[]),'
    b'setHeader:(name,value)=>setRequestScriptHeader(scriptHeaders,name,value)},c.jp=jpath',
)
for original, replacement in (
    (b'async function B(O,N,R){var', b'async function B(O,N,R){const scriptHeaders=new Map();var'),
    (b'le.requestScript,!0,N,R)}if(te.data.requestScript)',
     b'le.requestScript,!0,N,R,scriptHeaders)}if(te.data.requestScript)'),
    (b'await P(te,te.data.requestScript,!1,N,R)', b'await P(te,te.data.requestScript,!1,N,R,scriptHeaders)'),
    (b'case"server":Y=await k(te,N);', b'case"server":Y=await k(te,N,scriptHeaders);'),
    (b'Q.timeout);break;default:throw Error("Unknown proxy")',
     b'Q.timeout,scriptHeaders);break;default:throw Error("Unknown proxy")'),
    (b'async function P(O,N,R,V,J){await executeRequestScript',
     b'async function P(O,N,R,V,J,scriptHeaders){await executeRequestScript'),
    (b'await B(oe,Y,J+1)},R,V)}', b'await B(oe,Y,J+1)},R,V,scriptHeaders)}'),
    (b'async function C(O,N,R=5){return new Promise', b'async function C(O,N,R=5,scriptHeaders){return new Promise'),
    (b'}switch(X.data.contentType){', b'}applyRequestScriptHeaders(X,scriptHeaders);switch(X.data.contentType){'),
    (b'async function k(O,N){var R,V;', b'async function k(O,N,scriptHeaders){var R,V;'),
    (b'}switch(O.data.contentType){', b'}applyRequestScriptHeaders(O,scriptHeaders);switch(O.data.contentType){'),
):
    bundle = replace_once(bundle, original, replacement)

patched_asset = b'assets/index.' + sha256(bundle).hexdigest()[:12].encode('ascii') + b'.js'
index = replace_once(read('index.html'), asset, patched_asset)
write(patched_asset, bundle)
write('index.html', index)
