from hashlib import sha256


def read(path):
    with open(path, 'rb') as file:
        return file.read()


def write(path, content):
    with open(path, 'wb') as file:
        file.write(content)


def replace_once(content, original, replacement):
    if content.count(original) != 1:
        raise SystemExit('Unexpected Yaade web assets. Review the response display patch.')
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

patched_asset = b'assets/index.' + sha256(bundle).hexdigest()[:12].encode('ascii') + b'.js'
index = replace_once(read('index.html'), asset, patched_asset)
write(patched_asset, bundle)
write('index.html', index)
