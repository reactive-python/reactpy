(function(){const te=document.createElement("link").relList;if(te&&te.supports&&te.supports("modulepreload"))return;for(const ie of document.querySelectorAll('link[rel="modulepreload"]'))re(ie);new MutationObserver(ie=>{for(const oe of ie)if(oe.type==="childList")for(const ae of oe.addedNodes)ae.tagName==="LINK"&&ae.rel==="modulepreload"&&re(ae)}).observe(document,{childList:!0,subtree:!0});function ne(ie){const oe={};return ie.integrity&&(oe.integrity=ie.integrity),ie.referrerpolicy&&(oe.referrerPolicy=ie.referrerpolicy),ie.crossorigin==="use-credentials"?oe.credentials="include":ie.crossorigin==="anonymous"?oe.credentials="omit":oe.credentials="same-origin",oe}function re(ie){if(ie.ep)return;ie.ep=!0;const oe=ne(ie);fetch(ie.href,oe)}})();var n$1,l$1,u$1,t$2,o$1,r$1,f$1,e$1={},c$1=[],s$1=/acit|ex(?:s|g|n|p|$)|rph|grid|ows|mnc|ntw|ine[ch]|zoo|^ord|itera/i;function a$1(ee,te){for(var ne in te)ee[ne]=te[ne];return ee}function h$1(ee){var te=ee.parentNode;te&&te.removeChild(ee)}function v$1(ee,te,ne){var re,ie,oe,ae={};for(oe in te)oe=="key"?re=te[oe]:oe=="ref"?ie=te[oe]:ae[oe]=te[oe];if(arguments.length>2&&(ae.children=arguments.length>3?n$1.call(arguments,2):ne),typeof ee=="function"&&ee.defaultProps!=null)for(oe in ee.defaultProps)ae[oe]===void 0&&(ae[oe]=ee.defaultProps[oe]);return y$1(ee,ae,re,ie,null)}function y$1(ee,te,ne,re,ie){var oe={type:ee,props:te,key:ne,ref:re,__k:null,__:null,__b:0,__e:null,__d:void 0,__c:null,__h:null,constructor:void 0,__v:ie==null?++u$1:ie};return ie==null&&l$1.vnode!=null&&l$1.vnode(oe),oe}function p$1(){return{current:null}}function d$1(ee){return ee.children}function _$1(ee,te){this.props=ee,this.context=te}function k$2(ee,te){if(te==null)return ee.__?k$2(ee.__,ee.__.__k.indexOf(ee)+1):null;for(var ne;te<ee.__k.length;te++)if((ne=ee.__k[te])!=null&&ne.__e!=null)return ne.__e;return typeof ee.type=="function"?k$2(ee):null}function b$1(ee){var te,ne;if((ee=ee.__)!=null&&ee.__c!=null){for(ee.__e=ee.__c.base=null,te=0;te<ee.__k.length;te++)if((ne=ee.__k[te])!=null&&ne.__e!=null){ee.__e=ee.__c.base=ne.__e;break}return b$1(ee)}}function m$1(ee){(!ee.__d&&(ee.__d=!0)&&t$2.push(ee)&&!g$2.__r++||r$1!==l$1.debounceRendering)&&((r$1=l$1.debounceRendering)||o$1)(g$2)}function g$2(){for(var ee;g$2.__r=t$2.length;)ee=t$2.sort(function(te,ne){return te.__v.__b-ne.__v.__b}),t$2=[],ee.some(function(te){var ne,re,ie,oe,ae,ue;te.__d&&(ae=(oe=(ne=te).__v).__e,(ue=ne.__P)&&(re=[],(ie=a$1({},oe)).__v=oe.__v+1,j$2(ue,oe,ie,ne.__n,ue.ownerSVGElement!==void 0,oe.__h!=null?[ae]:null,re,ae==null?k$2(oe):ae,oe.__h),z$1(re,oe),oe.__e!=ae&&b$1(oe)))})}function w$2(ee,te,ne,re,ie,oe,ae,ue,le,fe){var ce,de,se,_e,pe,ve,me,he=re&&re.__k||c$1,$e=he.length;for(ne.__k=[],ce=0;ce<te.length;ce++)if((_e=ne.__k[ce]=(_e=te[ce])==null||typeof _e=="boolean"?null:typeof _e=="string"||typeof _e=="number"||typeof _e=="bigint"?y$1(null,_e,null,null,_e):Array.isArray(_e)?y$1(d$1,{children:_e},null,null,null):_e.__b>0?y$1(_e.type,_e.props,_e.key,null,_e.__v):_e)!=null){if(_e.__=ne,_e.__b=ne.__b+1,(se=he[ce])===null||se&&_e.key==se.key&&_e.type===se.type)he[ce]=void 0;else for(de=0;de<$e;de++){if((se=he[de])&&_e.key==se.key&&_e.type===se.type){he[de]=void 0;break}se=null}j$2(ee,_e,se=se||e$1,ie,oe,ae,ue,le,fe),pe=_e.__e,(de=_e.ref)&&se.ref!=de&&(me||(me=[]),se.ref&&me.push(se.ref,null,_e),me.push(de,_e.__c||pe,_e)),pe!=null?(ve==null&&(ve=pe),typeof _e.type=="function"&&_e.__k===se.__k?_e.__d=le=x$2(_e,le,ee):le=P$1(ee,_e,se,he,pe,le),typeof ne.type=="function"&&(ne.__d=le)):le&&se.__e==le&&le.parentNode!=ee&&(le=k$2(se))}for(ne.__e=ve,ce=$e;ce--;)he[ce]!=null&&(typeof ne.type=="function"&&he[ce].__e!=null&&he[ce].__e==ne.__d&&(ne.__d=k$2(re,ce+1)),N$1(he[ce],he[ce]));if(me)for(ce=0;ce<me.length;ce++)M$1(me[ce],me[++ce],me[++ce])}function x$2(ee,te,ne){for(var re,ie=ee.__k,oe=0;ie&&oe<ie.length;oe++)(re=ie[oe])&&(re.__=ee,te=typeof re.type=="function"?x$2(re,te,ne):P$1(ne,re,re,ie,re.__e,te));return te}function A$2(ee,te){return te=te||[],ee==null||typeof ee=="boolean"||(Array.isArray(ee)?ee.some(function(ne){A$2(ne,te)}):te.push(ee)),te}function P$1(ee,te,ne,re,ie,oe){var ae,ue,le;if(te.__d!==void 0)ae=te.__d,te.__d=void 0;else if(ne==null||ie!=oe||ie.parentNode==null)e:if(oe==null||oe.parentNode!==ee)ee.appendChild(ie),ae=null;else{for(ue=oe,le=0;(ue=ue.nextSibling)&&le<re.length;le+=2)if(ue==ie)break e;ee.insertBefore(ie,oe),ae=oe}return ae!==void 0?ae:ie.nextSibling}function C$1(ee,te,ne,re,ie){var oe;for(oe in ne)oe==="children"||oe==="key"||oe in te||H$1(ee,oe,null,ne[oe],re);for(oe in te)ie&&typeof te[oe]!="function"||oe==="children"||oe==="key"||oe==="value"||oe==="checked"||ne[oe]===te[oe]||H$1(ee,oe,te[oe],ne[oe],re)}function $$1(ee,te,ne){te[0]==="-"?ee.setProperty(te,ne):ee[te]=ne==null?"":typeof ne!="number"||s$1.test(te)?ne:ne+"px"}function H$1(ee,te,ne,re,ie){var oe;e:if(te==="style")if(typeof ne=="string")ee.style.cssText=ne;else{if(typeof re=="string"&&(ee.style.cssText=re=""),re)for(te in re)ne&&te in ne||$$1(ee.style,te,"");if(ne)for(te in ne)re&&ne[te]===re[te]||$$1(ee.style,te,ne[te])}else if(te[0]==="o"&&te[1]==="n")oe=te!==(te=te.replace(/Capture$/,"")),te=te.toLowerCase()in ee?te.toLowerCase().slice(2):te.slice(2),ee.l||(ee.l={}),ee.l[te+oe]=ne,ne?re||ee.addEventListener(te,oe?T$2:I$1,oe):ee.removeEventListener(te,oe?T$2:I$1,oe);else if(te!=="dangerouslySetInnerHTML"){if(ie)te=te.replace(/xlink(H|:h)/,"h").replace(/sName$/,"s");else if(te!=="href"&&te!=="list"&&te!=="form"&&te!=="tabIndex"&&te!=="download"&&te in ee)try{ee[te]=ne==null?"":ne;break e}catch{}typeof ne=="function"||(ne!=null&&(ne!==!1||te[0]==="a"&&te[1]==="r")?ee.setAttribute(te,ne):ee.removeAttribute(te))}}function I$1(ee){this.l[ee.type+!1](l$1.event?l$1.event(ee):ee)}function T$2(ee){this.l[ee.type+!0](l$1.event?l$1.event(ee):ee)}function j$2(ee,te,ne,re,ie,oe,ae,ue,le){var fe,ce,de,se,_e,pe,ve,me,he,$e,ge,ye=te.type;if(te.constructor!==void 0)return null;ne.__h!=null&&(le=ne.__h,ue=te.__e=ne.__e,te.__h=null,oe=[ue]),(fe=l$1.__b)&&fe(te);try{e:if(typeof ye=="function"){if(me=te.props,he=(fe=ye.contextType)&&re[fe.__c],$e=fe?he?he.props.value:fe.__:re,ne.__c?ve=(ce=te.__c=ne.__c).__=ce.__E:("prototype"in ye&&ye.prototype.render?te.__c=ce=new ye(me,$e):(te.__c=ce=new _$1(me,$e),ce.constructor=ye,ce.render=O$1),he&&he.sub(ce),ce.props=me,ce.state||(ce.state={}),ce.context=$e,ce.__n=re,de=ce.__d=!0,ce.__h=[]),ce.__s==null&&(ce.__s=ce.state),ye.getDerivedStateFromProps!=null&&(ce.__s==ce.state&&(ce.__s=a$1({},ce.__s)),a$1(ce.__s,ye.getDerivedStateFromProps(me,ce.__s))),se=ce.props,_e=ce.state,de)ye.getDerivedStateFromProps==null&&ce.componentWillMount!=null&&ce.componentWillMount(),ce.componentDidMount!=null&&ce.__h.push(ce.componentDidMount);else{if(ye.getDerivedStateFromProps==null&&me!==se&&ce.componentWillReceiveProps!=null&&ce.componentWillReceiveProps(me,$e),!ce.__e&&ce.shouldComponentUpdate!=null&&ce.shouldComponentUpdate(me,ce.__s,$e)===!1||te.__v===ne.__v){ce.props=me,ce.state=ce.__s,te.__v!==ne.__v&&(ce.__d=!1),ce.__v=te,te.__e=ne.__e,te.__k=ne.__k,te.__k.forEach(function(Ee){Ee&&(Ee.__=te)}),ce.__h.length&&ae.push(ce);break e}ce.componentWillUpdate!=null&&ce.componentWillUpdate(me,ce.__s,$e),ce.componentDidUpdate!=null&&ce.__h.push(function(){ce.componentDidUpdate(se,_e,pe)})}ce.context=$e,ce.props=me,ce.state=ce.__s,(fe=l$1.__r)&&fe(te),ce.__d=!1,ce.__v=te,ce.__P=ee,fe=ce.render(ce.props,ce.state,ce.context),ce.state=ce.__s,ce.getChildContext!=null&&(re=a$1(a$1({},re),ce.getChildContext())),de||ce.getSnapshotBeforeUpdate==null||(pe=ce.getSnapshotBeforeUpdate(se,_e)),ge=fe!=null&&fe.type===d$1&&fe.key==null?fe.props.children:fe,w$2(ee,Array.isArray(ge)?ge:[ge],te,ne,re,ie,oe,ae,ue,le),ce.base=te.__e,te.__h=null,ce.__h.length&&ae.push(ce),ve&&(ce.__E=ce.__=null),ce.__e=!1}else oe==null&&te.__v===ne.__v?(te.__k=ne.__k,te.__e=ne.__e):te.__e=L$1(ne.__e,te,ne,re,ie,oe,ae,le);(fe=l$1.diffed)&&fe(te)}catch(Ee){te.__v=null,(le||oe!=null)&&(te.__e=ue,te.__h=!!le,oe[oe.indexOf(ue)]=null),l$1.__e(Ee,te,ne)}}function z$1(ee,te){l$1.__c&&l$1.__c(te,ee),ee.some(function(ne){try{ee=ne.__h,ne.__h=[],ee.some(function(re){re.call(ne)})}catch(re){l$1.__e(re,ne.__v)}})}function L$1(ee,te,ne,re,ie,oe,ae,ue){var le,fe,ce,de=ne.props,se=te.props,_e=te.type,pe=0;if(_e==="svg"&&(ie=!0),oe!=null){for(;pe<oe.length;pe++)if((le=oe[pe])&&"setAttribute"in le==!!_e&&(_e?le.localName===_e:le.nodeType===3)){ee=le,oe[pe]=null;break}}if(ee==null){if(_e===null)return document.createTextNode(se);ee=ie?document.createElementNS("http://www.w3.org/2000/svg",_e):document.createElement(_e,se.is&&se),oe=null,ue=!1}if(_e===null)de===se||ue&&ee.data===se||(ee.data=se);else{if(oe=oe&&n$1.call(ee.childNodes),fe=(de=ne.props||e$1).dangerouslySetInnerHTML,ce=se.dangerouslySetInnerHTML,!ue){if(oe!=null)for(de={},pe=0;pe<ee.attributes.length;pe++)de[ee.attributes[pe].name]=ee.attributes[pe].value;(ce||fe)&&(ce&&(fe&&ce.__html==fe.__html||ce.__html===ee.innerHTML)||(ee.innerHTML=ce&&ce.__html||""))}if(C$1(ee,se,de,ie,ue),ce)te.__k=[];else if(pe=te.props.children,w$2(ee,Array.isArray(pe)?pe:[pe],te,ne,re,ie&&_e!=="foreignObject",oe,ae,oe?oe[0]:ne.__k&&k$2(ne,0),ue),oe!=null)for(pe=oe.length;pe--;)oe[pe]!=null&&h$1(oe[pe]);ue||("value"in se&&(pe=se.value)!==void 0&&(pe!==ee.value||_e==="progress"&&!pe||_e==="option"&&pe!==de.value)&&H$1(ee,"value",pe,de.value,!1),"checked"in se&&(pe=se.checked)!==void 0&&pe!==ee.checked&&H$1(ee,"checked",pe,de.checked,!1))}return ee}function M$1(ee,te,ne){try{typeof ee=="function"?ee(te):ee.current=te}catch(re){l$1.__e(re,ne)}}function N$1(ee,te,ne){var re,ie;if(l$1.unmount&&l$1.unmount(ee),(re=ee.ref)&&(re.current&&re.current!==ee.__e||M$1(re,null,te)),(re=ee.__c)!=null){if(re.componentWillUnmount)try{re.componentWillUnmount()}catch(oe){l$1.__e(oe,te)}re.base=re.__P=null}if(re=ee.__k)for(ie=0;ie<re.length;ie++)re[ie]&&N$1(re[ie],te,typeof ee.type!="function");ne||ee.__e==null||h$1(ee.__e),ee.__e=ee.__d=void 0}function O$1(ee,te,ne){return this.constructor(ee,ne)}function S$1(ee,te,ne){var re,ie,oe;l$1.__&&l$1.__(ee,te),ie=(re=typeof ne=="function")?null:ne&&ne.__k||te.__k,oe=[],j$2(te,ee=(!re&&ne||te).__k=v$1(d$1,null,[ee]),ie||e$1,e$1,te.ownerSVGElement!==void 0,!re&&ne?[ne]:ie?null:te.firstChild?n$1.call(te.childNodes):null,oe,!re&&ne?ne:ie?ie.__e:te.firstChild,re),z$1(oe,ee)}function q$1(ee,te){S$1(ee,te,q$1)}function B$1(ee,te,ne){var re,ie,oe,ae=a$1({},ee.props);for(oe in te)oe=="key"?re=te[oe]:oe=="ref"?ie=te[oe]:ae[oe]=te[oe];return arguments.length>2&&(ae.children=arguments.length>3?n$1.call(arguments,2):ne),y$1(ee.type,ae,re||ee.key,ie||ee.ref,null)}function D$1(ee,te){var ne={__c:te="__cC"+f$1++,__:ee,Consumer:function(re,ie){return re.children(ie)},Provider:function(re){var ie,oe;return this.getChildContext||(ie=[],(oe={})[te]=this,this.getChildContext=function(){return oe},this.shouldComponentUpdate=function(ae){this.props.value!==ae.value&&ie.some(m$1)},this.sub=function(ae){ie.push(ae);var ue=ae.componentWillUnmount;ae.componentWillUnmount=function(){ie.splice(ie.indexOf(ae),1),ue&&ue.call(ae)}}),re.children}};return ne.Provider.__=ne.Consumer.contextType=ne}n$1=c$1.slice,l$1={__e:function(ee,te,ne,re){for(var ie,oe,ae;te=te.__;)if((ie=te.__c)&&!ie.__)try{if((oe=ie.constructor)&&oe.getDerivedStateFromError!=null&&(ie.setState(oe.getDerivedStateFromError(ee)),ae=ie.__d),ie.componentDidCatch!=null&&(ie.componentDidCatch(ee,re||{}),ae=ie.__d),ae)return ie.__E=ie}catch(ue){ee=ue}throw ee}},u$1=0,_$1.prototype.setState=function(ee,te){var ne;ne=this.__s!=null&&this.__s!==this.state?this.__s:this.__s=a$1({},this.state),typeof ee=="function"&&(ee=ee(a$1({},ne),this.props)),ee&&a$1(ne,ee),ee!=null&&this.__v&&(te&&this.__h.push(te),m$1(this))},_$1.prototype.forceUpdate=function(ee){this.__v&&(this.__e=!0,ee&&this.__h.push(ee),m$1(this))},_$1.prototype.render=d$1,t$2=[],o$1=typeof Promise=="function"?Promise.prototype.then.bind(Promise.resolve()):setTimeout,g$2.__r=0,f$1=0;var t$1,u,r,o=0,i=[],c=l$1.__b,f=l$1.__r,e=l$1.diffed,a=l$1.__c,v=l$1.unmount;function l(ee,te){l$1.__h&&l$1.__h(u,ee,o||te),o=0;var ne=u.__H||(u.__H={__:[],__h:[]});return ee>=ne.__.length&&ne.__.push({}),ne.__[ee]}function m(ee){return o=1,p(w$1,ee)}function p(ee,te,ne){var re=l(t$1++,2);return re.t=ee,re.__c||(re.__=[ne?ne(te):w$1(void 0,te),function(ie){var oe=re.t(re.__[0],ie);re.__[0]!==oe&&(re.__=[oe,re.__[1]],re.__c.setState({}))}],re.__c=u),re.__}function y(ee,te){var ne=l(t$1++,3);!l$1.__s&&k$1(ne.__H,te)&&(ne.__=ee,ne.__H=te,u.__H.__h.push(ne))}function d(ee,te){var ne=l(t$1++,4);!l$1.__s&&k$1(ne.__H,te)&&(ne.__=ee,ne.__H=te,u.__h.push(ne))}function h(ee){return o=5,_(function(){return{current:ee}},[])}function s(ee,te,ne){o=6,d(function(){return typeof ee=="function"?(ee(te()),function(){return ee(null)}):ee?(ee.current=te(),function(){return ee.current=null}):void 0},ne==null?ne:ne.concat(ee))}function _(ee,te){var ne=l(t$1++,7);return k$1(ne.__H,te)&&(ne.__=ee(),ne.__H=te,ne.__h=ee),ne.__}function A$1(ee,te){return o=8,_(function(){return ee},te)}function F$1(ee){var te=u.context[ee.__c],ne=l(t$1++,9);return ne.c=ee,te?(ne.__==null&&(ne.__=!0,te.sub(u)),te.props.value):ee.__}function T$1(ee,te){l$1.useDebugValue&&l$1.useDebugValue(te?te(ee):ee)}function x$1(){for(var ee;ee=i.shift();)if(ee.__P)try{ee.__H.__h.forEach(g$1),ee.__H.__h.forEach(j$1),ee.__H.__h=[]}catch(te){ee.__H.__h=[],l$1.__e(te,ee.__v)}}l$1.__b=function(ee){u=null,c&&c(ee)},l$1.__r=function(ee){f&&f(ee),t$1=0;var te=(u=ee.__c).__H;te&&(te.__h.forEach(g$1),te.__h.forEach(j$1),te.__h=[])},l$1.diffed=function(ee){e&&e(ee);var te=ee.__c;te&&te.__H&&te.__H.__h.length&&(i.push(te)!==1&&r===l$1.requestAnimationFrame||((r=l$1.requestAnimationFrame)||function(ne){var re,ie=function(){clearTimeout(oe),b&&cancelAnimationFrame(re),setTimeout(ne)},oe=setTimeout(ie,100);b&&(re=requestAnimationFrame(ie))})(x$1)),u=null},l$1.__c=function(ee,te){te.some(function(ne){try{ne.__h.forEach(g$1),ne.__h=ne.__h.filter(function(re){return!re.__||j$1(re)})}catch(re){te.some(function(ie){ie.__h&&(ie.__h=[])}),te=[],l$1.__e(re,ne.__v)}}),a&&a(ee,te)},l$1.unmount=function(ee){v&&v(ee);var te,ne=ee.__c;ne&&ne.__H&&(ne.__H.__.forEach(function(re){try{g$1(re)}catch(ie){te=ie}}),te&&l$1.__e(te,ne.__v))};var b=typeof requestAnimationFrame=="function";function g$1(ee){var te=u,ne=ee.__c;typeof ne=="function"&&(ee.__c=void 0,ne()),u=te}function j$1(ee){var te=u;ee.__c=ee.__(),u=te}function k$1(ee,te){return!ee||ee.length!==te.length||te.some(function(ne,re){return ne!==ee[re]})}function w$1(ee,te){return typeof te=="function"?te(ee):te}function C(ee,te){for(var ne in te)ee[ne]=te[ne];return ee}function S(ee,te){for(var ne in ee)if(ne!=="__source"&&!(ne in te))return!0;for(var re in te)if(re!=="__source"&&ee[re]!==te[re])return!0;return!1}function E(ee){this.props=ee}function g(ee,te){function ne(ie){var oe=this.props.ref,ae=oe==ie.ref;return!ae&&oe&&(oe.call?oe(null):oe.current=null),te?!te(this.props,ie)||!ae:S(this.props,ie)}function re(ie){return this.shouldComponentUpdate=ne,v$1(ee,ie)}return re.displayName="Memo("+(ee.displayName||ee.name)+")",re.prototype.isReactComponent=!0,re.__f=!0,re}(E.prototype=new _$1).isPureReactComponent=!0,E.prototype.shouldComponentUpdate=function(ee,te){return S(this.props,ee)||S(this.state,te)};var w=l$1.__b;l$1.__b=function(ee){ee.type&&ee.type.__f&&ee.ref&&(ee.props.ref=ee.ref,ee.ref=null),w&&w(ee)};var R=typeof Symbol<"u"&&Symbol.for&&Symbol.for("react.forward_ref")||3911;function x(ee){function te(ne,re){var ie=C({},ne);return delete ie.ref,ee(ie,!(re=ne.ref||re)||typeof re=="object"&&Object.keys(re).length===0?null:re)}return te.$$typeof=R,te.render=te,te.prototype.isReactComponent=te.__f=!0,te.displayName="ForwardRef("+(ee.displayName||ee.name)+")",te}var N=function(ee,te){return ee==null?null:A$2(A$2(ee).map(te))},k={map:N,forEach:N,count:function(ee){return ee?A$2(ee).length:0},only:function(ee){var te=A$2(ee);if(te.length!==1)throw"Children.only";return te[0]},toArray:A$2},O=l$1.__e;l$1.__e=function(ee,te,ne,re){if(ee.then){for(var ie,oe=te;oe=oe.__;)if((ie=oe.__c)&&ie.__c)return te.__e==null&&(te.__e=ne.__e,te.__k=ne.__k),ie.__c(ee,te)}O(ee,te,ne,re)};var A=l$1.unmount;function L(){this.__u=0,this.t=null,this.__b=null}function U(ee){var te=ee.__.__c;return te&&te.__e&&te.__e(ee)}function F(ee){var te,ne,re;function ie(oe){if(te||(te=ee()).then(function(ae){ne=ae.default||ae},function(ae){re=ae}),re)throw re;if(!ne)throw te;return v$1(ne,oe)}return ie.displayName="Lazy",ie.__f=!0,ie}function M(){this.u=null,this.o=null}l$1.unmount=function(ee){var te=ee.__c;te&&te.__R&&te.__R(),te&&ee.__h===!0&&(ee.type=null),A&&A(ee)},(L.prototype=new _$1).__c=function(ee,te){var ne=te.__c,re=this;re.t==null&&(re.t=[]),re.t.push(ne);var ie=U(re.__v),oe=!1,ae=function(){oe||(oe=!0,ne.__R=null,ie?ie(ue):ue())};ne.__R=ae;var ue=function(){if(!--re.__u){if(re.state.__e){var fe=re.state.__e;re.__v.__k[0]=function de(se,_e,pe){return se&&(se.__v=null,se.__k=se.__k&&se.__k.map(function(ve){return de(ve,_e,pe)}),se.__c&&se.__c.__P===_e&&(se.__e&&pe.insertBefore(se.__e,se.__d),se.__c.__e=!0,se.__c.__P=pe)),se}(fe,fe.__c.__P,fe.__c.__O)}var ce;for(re.setState({__e:re.__b=null});ce=re.t.pop();)ce.forceUpdate()}},le=te.__h===!0;re.__u++||le||re.setState({__e:re.__b=re.__v.__k[0]}),ee.then(ae,ae)},L.prototype.componentWillUnmount=function(){this.t=[]},L.prototype.render=function(ee,te){if(this.__b){if(this.__v.__k){var ne=document.createElement("div"),re=this.__v.__k[0].__c;this.__v.__k[0]=function oe(ae,ue,le){return ae&&(ae.__c&&ae.__c.__H&&(ae.__c.__H.__.forEach(function(fe){typeof fe.__c=="function"&&fe.__c()}),ae.__c.__H=null),(ae=C({},ae)).__c!=null&&(ae.__c.__P===le&&(ae.__c.__P=ue),ae.__c=null),ae.__k=ae.__k&&ae.__k.map(function(fe){return oe(fe,ue,le)})),ae}(this.__b,ne,re.__O=re.__P)}this.__b=null}var ie=te.__e&&v$1(d$1,null,ee.fallback);return ie&&(ie.__h=null),[v$1(d$1,null,te.__e?null:ee.children),ie]};var T=function(ee,te,ne){if(++ne[1]===ne[0]&&ee.o.delete(te),ee.props.revealOrder&&(ee.props.revealOrder[0]!=="t"||!ee.o.size))for(ne=ee.u;ne;){for(;ne.length>3;)ne.pop()();if(ne[1]<ne[0])break;ee.u=ne=ne[2]}};function j(ee){return this.getChildContext=function(){return ee.context},ee.children}function D(ee){var te=this,ne=ee.i;te.componentWillUnmount=function(){S$1(null,te.l),te.l=null,te.i=null},te.i&&te.i!==ne&&te.componentWillUnmount(),ee.__v?(te.l||(te.i=ne,te.l={nodeType:1,parentNode:ne,childNodes:[],appendChild:function(re){this.childNodes.push(re),te.i.appendChild(re)},insertBefore:function(re,ie){this.childNodes.push(re),te.i.appendChild(re)},removeChild:function(re){this.childNodes.splice(this.childNodes.indexOf(re)>>>1,1),te.i.removeChild(re)}}),S$1(v$1(j,{context:te.context},ee.__v),te.l)):te.l&&te.componentWillUnmount()}function I(ee,te){return v$1(D,{__v:ee,i:te})}(M.prototype=new _$1).__e=function(ee){var te=this,ne=U(te.__v),re=te.o.get(ee);return re[0]++,function(ie){var oe=function(){te.props.revealOrder?(re.push(ie),T(te,ee,re)):ie()};ne?ne(oe):oe()}},M.prototype.render=function(ee){this.u=null,this.o=new Map;var te=A$2(ee.children);ee.revealOrder&&ee.revealOrder[0]==="b"&&te.reverse();for(var ne=te.length;ne--;)this.o.set(te[ne],this.u=[1,0,this.u]);return ee.children},M.prototype.componentDidUpdate=M.prototype.componentDidMount=function(){var ee=this;this.o.forEach(function(te,ne){T(ee,ne,te)})};var W=typeof Symbol<"u"&&Symbol.for&&Symbol.for("react.element")||60103,P=/^(?:accent|alignment|arabic|baseline|cap|clip(?!PathU)|color|dominant|fill|flood|font|glyph(?!R)|horiz|marker(?!H|W|U)|overline|paint|stop|strikethrough|stroke|text(?!L)|underline|unicode|units|v|vector|vert|word|writing|x(?!C))[A-Z]/,V=typeof document<"u",z=function(ee){return(typeof Symbol<"u"&&typeof Symbol()=="symbol"?/fil|che|rad/i:/fil|che|ra/i).test(ee)};function B(ee,te,ne){return te.__k==null&&(te.textContent=""),S$1(ee,te),typeof ne=="function"&&ne(),ee?ee.__c:null}function $(ee,te,ne){return q$1(ee,te),typeof ne=="function"&&ne(),ee?ee.__c:null}_$1.prototype.isReactComponent={},["componentWillMount","componentWillReceiveProps","componentWillUpdate"].forEach(function(ee){Object.defineProperty(_$1.prototype,ee,{configurable:!0,get:function(){return this["UNSAFE_"+ee]},set:function(te){Object.defineProperty(this,ee,{configurable:!0,writable:!0,value:te})}})});var H=l$1.event;function Z(){}function Y(){return this.cancelBubble}function q(){return this.defaultPrevented}l$1.event=function(ee){return H&&(ee=H(ee)),ee.persist=Z,ee.isPropagationStopped=Y,ee.isDefaultPrevented=q,ee.nativeEvent=ee};var G,J={configurable:!0,get:function(){return this.class}},K=l$1.vnode;l$1.vnode=function(ee){var te=ee.type,ne=ee.props,re=ne;if(typeof te=="string"){var ie=te.indexOf("-")===-1;for(var oe in re={},ne){var ae=ne[oe];V&&oe==="children"&&te==="noscript"||oe==="value"&&"defaultValue"in ne&&ae==null||(oe==="defaultValue"&&"value"in ne&&ne.value==null?oe="value":oe==="download"&&ae===!0?ae="":/ondoubleclick/i.test(oe)?oe="ondblclick":/^onchange(textarea|input)/i.test(oe+te)&&!z(ne.type)?oe="oninput":/^onfocus$/i.test(oe)?oe="onfocusin":/^onblur$/i.test(oe)?oe="onfocusout":/^on(Ani|Tra|Tou|BeforeInp|Compo)/.test(oe)?oe=oe.toLowerCase():ie&&P.test(oe)?oe=oe.replace(/[A-Z0-9]/,"-$&").toLowerCase():ae===null&&(ae=void 0),re[oe]=ae)}te=="select"&&re.multiple&&Array.isArray(re.value)&&(re.value=A$2(ne.children).forEach(function(ue){ue.props.selected=re.value.indexOf(ue.props.value)!=-1})),te=="select"&&re.defaultValue!=null&&(re.value=A$2(ne.children).forEach(function(ue){ue.props.selected=re.multiple?re.defaultValue.indexOf(ue.props.value)!=-1:re.defaultValue==ue.props.value})),ee.props=re,ne.class!=ne.className&&(J.enumerable="className"in ne,ne.className!=null&&(re.class=ne.className),Object.defineProperty(re,"className",J))}ee.$$typeof=W,K&&K(ee)};var Q=l$1.__r;l$1.__r=function(ee){Q&&Q(ee),G=ee.__c};var X={ReactCurrentDispatcher:{current:{readContext:function(ee){return G.__n[ee.__c].props.value}}}};function tn(ee){return v$1.bind(null,ee)}function en(ee){return!!ee&&ee.$$typeof===W}function rn(ee){return en(ee)?B$1.apply(null,arguments):ee}function un(ee){return!!ee.__k&&(S$1(null,ee),!0)}function on(ee){return ee&&(ee.base||ee.nodeType===1&&ee)||null}var ln=function(ee,te){return ee(te)},cn=function(ee,te){return ee(te)};const ReactDOM={useState:m,useReducer:p,useEffect:y,useLayoutEffect:d,useRef:h,useImperativeHandle:s,useMemo:_,useCallback:A$1,useContext:F$1,useDebugValue:T$1,version:"17.0.2",Children:k,render:B,hydrate:$,unmountComponentAtNode:un,createPortal:I,createElement:v$1,createContext:D$1,createFactory:tn,cloneElement:rn,createRef:p$1,Fragment:d$1,isValidElement:en,findDOMNode:on,Component:_$1,PureComponent:E,memo:g,forwardRef:x,flushSync:cn,unstable_batchedUpdates:ln,StrictMode:d$1,Suspense:L,SuspenseList:M,lazy:F,__SECRET_INTERNALS_DO_NOT_USE_OR_YOU_WILL_BE_FIRED:X};var n=function(ee,te,ne,re){var ie;te[0]=0;for(var oe=1;oe<te.length;oe++){var ae=te[oe++],ue=te[oe]?(te[0]|=ae?1:2,ne[te[oe++]]):te[++oe];ae===3?re[0]=ue:ae===4?re[1]=Object.assign(re[1]||{},ue):ae===5?(re[1]=re[1]||{})[te[++oe]]=ue:ae===6?re[1][te[++oe]]+=ue+"":ae?(ie=ee.apply(ue,n(ee,ue,ne,["",null])),re.push(ie),ue[0]?te[0]|=2:(te[oe-2]=0,te[oe]=ie)):re.push(ue)}return re},t=new Map;function htm(ee){var te=t.get(this);return te||(te=new Map,t.set(this,te)),(te=n(this,te.get(ee)||(te.set(ee,te=function(ne){for(var re,ie,oe=1,ae="",ue="",le=[0],fe=function(se){oe===1&&(se||(ae=ae.replace(/^\s*\n\s*|\s*\n\s*$/g,"")))?le.push(0,se,ae):oe===3&&(se||ae)?(le.push(3,se,ae),oe=2):oe===2&&ae==="..."&&se?le.push(4,se,0):oe===2&&ae&&!se?le.push(5,0,!0,ae):oe>=5&&((ae||!se&&oe===5)&&(le.push(oe,0,ae,ie),oe=6),se&&(le.push(oe,se,0,ie),oe=6)),ae=""},ce=0;ce<ne.length;ce++){ce&&(oe===1&&fe(),fe(ce));for(var de=0;de<ne[ce].length;de++)re=ne[ce][de],oe===1?re==="<"?(fe(),le=[le],oe=3):ae+=re:oe===4?ae==="--"&&re===">"?(oe=1,ae=""):ae=re+ae[0]:ue?re===ue?ue="":ae+=re:re==='"'||re==="'"?ue=re:re===">"?(fe(),oe=1):oe&&(re==="="?(oe=5,ie=ae,ae=""):re==="/"&&(oe<5||ne[ce][de+1]===">")?(fe(),oe===3&&(le=le[0]),oe=le,(le=le[0]).push(2,0,oe),oe=0):re===" "||re==="	"||re===`
`||re==="\r"?(fe(),oe=2):ae+=re),oe===3&&ae==="!--"&&(oe=4,le=le[0])}return fe(),le}(ee)),te),arguments,[])).length>1?te:te[0]}var hasOwn=Object.prototype.hasOwnProperty,toString=Object.prototype.toString,foreach=function(te,ne,re){if(toString.call(ne)!=="[object Function]")throw new TypeError("iterator must be a function");var ie=te.length;if(ie===+ie)for(var oe=0;oe<ie;oe++)ne.call(re,te[oe],oe,te);else for(var ae in te)hasOwn.call(te,ae)&&ne.call(re,te[ae],ae,te)},each=foreach,jsonPointer=api;function api(ee,te,ne){if(arguments.length===3)return api.set(ee,te,ne);if(arguments.length===2)return api.get(ee,te);var re=api.bind(api,ee);for(var ie in api)api.hasOwnProperty(ie)&&(re[ie]=api[ie].bind(re,ee));return re}api.get=function(te,ne){for(var re=Array.isArray(ne)?ne:api.parse(ne),ie=0;ie<re.length;++ie){var oe=re[ie];if(!(typeof te=="object"&&oe in te))throw new Error("Invalid reference token: "+oe);te=te[oe]}return te};api.set=function(te,ne,re){var ie=Array.isArray(ne)?ne:api.parse(ne),oe=ie[0];if(ie.length===0)throw Error("Can not set the root object");for(var ae=0;ae<ie.length-1;++ae){var ue=ie[ae];typeof ue!="string"&&typeof ue!="number"&&(ue=String(ue)),!(ue==="__proto__"||ue==="constructor"||ue==="prototype")&&(ue==="-"&&Array.isArray(te)&&(ue=te.length),oe=ie[ae+1],ue in te||(oe.match(/^(\d+|-)$/)?te[ue]=[]:te[ue]={}),te=te[ue])}return oe==="-"&&Array.isArray(te)&&(oe=te.length),te[oe]=re,this};api.remove=function(ee,te){var ne=Array.isArray(te)?te:api.parse(te),re=ne[ne.length-1];if(re===void 0)throw new Error('Invalid JSON pointer for remove: "'+te+'"');var ie=api.get(ee,ne.slice(0,-1));if(Array.isArray(ie)){var oe=+re;if(re===""&&isNaN(oe))throw new Error('Invalid array index: "'+re+'"');Array.prototype.splice.call(ie,oe,1)}else delete ie[re]};api.dict=function(te,ne){var re={};return api.walk(te,function(ie,oe){re[oe]=ie},ne),re};api.walk=function(te,ne,re){var ie=[];re=re||function(oe){var ae=Object.prototype.toString.call(oe);return ae==="[object Object]"||ae==="[object Array]"},function oe(ae){each(ae,function(ue,le){ie.push(String(le)),re(ue)?oe(ue):ne(ue,api.compile(ie)),ie.pop()})}(te)};api.has=function(te,ne){try{api.get(te,ne)}catch{return!1}return!0};api.escape=function(te){return te.toString().replace(/~/g,"~0").replace(/\//g,"~1")};api.unescape=function(te){return te.replace(/~1/g,"/").replace(/~0/g,"~")};api.parse=function(te){if(te==="")return[];if(te.charAt(0)!=="/")throw new Error("Invalid JSON pointer: "+te);return te.substring(1).split(/\//).map(api.unescape)};api.compile=function(te){return te.length===0?"":"/"+te.map(api.escape).join("/")};const LayoutContext=ReactDOM.createContext({sendEvent:void 0,loadImportSource:void 0});function serializeEvent(ee){const te={};return ee.type in eventTransforms&&Object.assign(te,eventTransforms[ee.type](ee)),te.target=serializeDomElement(ee.target),te.currentTarget=ee.target===ee.currentTarget?te.target:serializeDomElement(ee.currentTarget),te.relatedTarget=serializeDomElement(ee.relatedTarget),te}function serializeDomElement(ee){let te=null;return ee&&(te=defaultElementTransform(ee),ee.tagName in elementTransforms&&elementTransforms[ee.tagName].forEach(ne=>Object.assign(te,ne(ee)))),te}const elementTransformCategories={hasValue:ee=>({value:ee.value}),hasCurrentTime:ee=>({currentTime:ee.currentTime}),hasFiles:ee=>(ee==null?void 0:ee.type)==="file"?{files:Array.from(ee.files).map(te=>({lastModified:te.lastModified,name:te.name,size:te.size,type:te.type}))}:{},hasElements:ee=>{const{elements:te}=ee;return{elements:[...Array(te.length).keys()].map(re=>serializeDomElement(te[re]))}},hasName:ee=>{const{name:te}=ee;return typeof te=="string"?{name:te}:{}}};function defaultElementTransform(ee){return{boundingClientRect:ee.getBoundingClientRect()}}const elementTagCategories={hasValue:["BUTTON","INPUT","OPTION","LI","METER","PROGRESS","PARAM","SELECT","TEXTAREA"],hasCurrentTime:["AUDIO","VIDEO"],hasFiles:["INPUT"],hasElements:["FORM"],hasName:["BUTTON","FORM","FIELDSET","IFRAME","INPUT","KEYGEN","OBJECT","OUTPUT","SELECT","TEXTAREA","MAP","META","PARAM"]},elementTransforms={};Object.keys(elementTagCategories).forEach(ee=>{elementTagCategories[ee].forEach(te=>{(elementTransforms[te]||(elementTransforms[te]=[])).push(elementTransformCategories[ee])})});function EventTransformCategories(){this.clipboard=ee=>({clipboardData:ee.clipboardData}),this.composition=ee=>({data:ee.data}),this.keyboard=ee=>({altKey:ee.altKey,charCode:ee.charCode,ctrlKey:ee.ctrlKey,key:ee.key,keyCode:ee.keyCode,locale:ee.locale,location:ee.location,metaKey:ee.metaKey,repeat:ee.repeat,shiftKey:ee.shiftKey,which:ee.which}),this.mouse=ee=>({altKey:ee.altKey,button:ee.button,buttons:ee.buttons,clientX:ee.clientX,clientY:ee.clientY,ctrlKey:ee.ctrlKey,metaKey:ee.metaKey,pageX:ee.pageX,pageY:ee.pageY,screenX:ee.screenX,screenY:ee.screenY,shiftKey:ee.shiftKey}),this.pointer=ee=>({...this.mouse(ee),pointerId:ee.pointerId,width:ee.width,height:ee.height,pressure:ee.pressure,tiltX:ee.tiltX,tiltY:ee.tiltY,pointerType:ee.pointerType,isPrimary:ee.isPrimary}),this.selection=()=>({selectedText:window.getSelection().toString()}),this.touch=ee=>({altKey:ee.altKey,ctrlKey:ee.ctrlKey,metaKey:ee.metaKey,shiftKey:ee.shiftKey}),this.ui=ee=>({detail:ee.detail}),this.wheel=ee=>({deltaMode:ee.deltaMode,deltaX:ee.deltaX,deltaY:ee.deltaY,deltaZ:ee.deltaZ}),this.animation=ee=>({animationName:ee.animationName,pseudoElement:ee.pseudoElement,elapsedTime:ee.elapsedTime}),this.transition=ee=>({propertyName:ee.propertyName,pseudoElement:ee.pseudoElement,elapsedTime:ee.elapsedTime})}const eventTypeCategories={clipboard:["copy","cut","paste"],composition:["compositionend","compositionstart","compositionupdate"],keyboard:["keydown","keypress","keyup"],mouse:["click","contextmenu","doubleclick","drag","dragend","dragenter","dragexit","dragleave","dragover","dragstart","drop","mousedown","mouseenter","mouseleave","mousemove","mouseout","mouseover","mouseup"],pointer:["pointerdown","pointermove","pointerup","pointercancel","gotpointercapture","lostpointercapture","pointerenter","pointerleave","pointerover","pointerout"],selection:["select"],touch:["touchcancel","touchend","touchmove","touchstart"],ui:["scroll"],wheel:["wheel"],animation:["animationstart","animationend","animationiteration"],transition:["transitionend"]},eventTransforms={},eventTransformCategories=new EventTransformCategories;Object.keys(eventTypeCategories).forEach(ee=>{eventTypeCategories[ee].forEach(te=>{eventTransforms[te]=eventTransformCategories[ee]})});function createElementChildren(ee,te){return ee.children?ee.children.filter(ne=>ne).map(ne=>{switch(typeof ne){case"object":return te(ne);case"string":return ne}}):[]}function createElementAttributes(ee,te){const ne=Object.assign({},ee.attributes);if(ee.eventHandlers)for(const[re,ie]of Object.entries(ee.eventHandlers))ne[re]=createEventHandler(te,ie);return Object.fromEntries(Object.entries(ne).map(normalizeAttribute))}function createEventHandler(ee,te){return function(){const ne=Array.from(arguments).map(re=>typeof re=="object"&&re.nativeEvent?(te.preventDefault&&re.preventDefault(),te.stopPropagation&&re.stopPropagation(),serializeEvent(re)):re);ee({data:ne,target:te.target})}}function normalizeAttribute([ee,te]){let ne=ee,re=te;return ee==="style"&&typeof te=="object"?re=Object.fromEntries(Object.entries(te).map(([ie,oe])=>[snakeToCamel(ie),oe])):ee.startsWith("data_")||ee.startsWith("aria_")||DASHED_HTML_ATTRS.includes(ee)?ne=ee.replaceAll("_","-"):ne=snakeToCamel(ee),[ne,re]}function snakeToCamel(ee){return ee.replace(/([_][a-z])/g,te=>te.toUpperCase().replace("_",""))}const DASHED_HTML_ATTRS=["accept_charset","http_equiv"];function useImportSource(ee){const te=ReactDOM.useContext(LayoutContext),[ne,re]=ReactDOM.useState(null);return ReactDOM.useEffect(()=>{let ie=!1;return loadModelImportSource(te,ee).then(oe=>{ie||re(oe)}),()=>{ie=!0}},[te,ee,re]),ne}function loadModelImportSource(ee,te){return ee.loadImportSource(te.source,te.sourceType).then(ne=>{if(typeof ne.bind=="function")return{data:te,bind:re=>{te.source,te.sourceType;const ie=ne.bind(re,ee);if(typeof ie.create=="function"&&typeof ie.render=="function"&&typeof ie.unmount=="function")return{render:oe=>ie.render(createElementFromModuleBinding(ee,te,ne,ie,oe)),unmount:ie.unmount};console.error(`${te.source} returned an impropper binding`)}};console.error(`${te.source} did not export a function 'bind'`)})}function createElementFromModuleBinding(ee,te,ne,re,ie){let oe;if(ie.importSource)if(isImportSourceEqual(te,ie.importSource))if(ne[ie.tagName])oe=ne[ie.tagName];else return console.error("Module from source "+stringifyImportSource(te)+` does not export ${ie.tagName}`),null;else return console.error("Parent element import source "+stringifyImportSource(te)+" does not match child's import source "+stringifyImportSource(ie.importSource)),null;else oe=ie.tagName;return re.create(oe,createElementAttributes(ie,ee.sendEvent),createElementChildren(ie,ae=>createElementFromModuleBinding(ee,te,ne,re,ae)))}function isImportSourceEqual(ee,te){return ee.source===te.source&&ee.sourceType===te.sourceType}function stringifyImportSource(ee){return JSON.stringify({source:ee.source,sourceType:ee.sourceType})}const html=htm.bind(ReactDOM.createElement);function Layout({saveUpdateHook:ee,sendEvent:te,loadImportSource:ne}){const re=ReactDOM.useState({})[0],ie=useForceUpdate(),oe=ReactDOM.useCallback(({path:ae,model:ue})=>{ae?jsonPointer.set(re,ae,ue):Object.assign(re,ue),ie()},[re]);return ReactDOM.useEffect(()=>ee(oe),[oe]),Object.keys(re).length?html`
    <${LayoutContext.Provider} value=${{sendEvent:te,loadImportSource:ne}}>
      <${Element} model=${re} />
    <//>
  `:html`<${ReactDOM.Fragment} />`}function Element({model:ee}){return ee.error!==void 0?ee.error?html`<pre>${ee.error}</pre>`:null:ee.tagName=="script"?html`<${ScriptElement} model=${ee} />`:["input","select","textarea"].includes(ee.tagName)?html`<${UserInputElement} model=${ee} />`:ee.importSource?html`<${ImportedElement} model=${ee} />`:html`<${StandardElement} model=${ee} />`}function StandardElement({model:ee}){const te=ReactDOM.useContext(LayoutContext);let ne;return ee.tagName==""?ne=ReactDOM.Fragment:ne=ee.tagName,ReactDOM.createElement(ne,createElementAttributes(ee,te.sendEvent),...createElementChildren(ee,re=>html`<${Element} key=${re.key} model=${re} />`))}function UserInputElement({model:ee}){const te=ReactDOM.useRef(),ne=ReactDOM.useContext(LayoutContext),re=createElementAttributes(ee,ne.sendEvent);let ie=re.value;delete re.value,ReactDOM.useEffect(()=>{ie!==void 0&&(te.current.value=ie)},[te.current,ie]);const oe=ReactDOM.useState([])[0];oe&&(ie===oe[0]?(oe.shift(),ie=oe[oe.length-1]):oe.length=0);const ae=re.onChange;return typeof ae=="function"&&(re.onChange=ue=>{oe.push(ue.target.value),ae(ue)}),ReactDOM.createElement(ee.tagName,{...re,ref:ue=>{te.current=ue}},...createElementChildren(ee,ue=>html`<${Element} key=${ue.key} model=${ue} />`))}function ScriptElement({model}){const ref=ReactDOM.useRef();return ReactDOM.useEffect(()=>{var ee,te;((ee=model==null?void 0:model.children)==null?void 0:ee.length)>1&&console.error("Too many children for 'script' element.");let scriptContent=(te=model==null?void 0:model.children)==null?void 0:te[0],scriptElement;if(model.attributes){scriptElement=document.createElement("script");for(const[ne,re]of Object.entries(model.attributes))scriptElement.setAttribute(ne,re);scriptElement.appendChild(document.createTextNode(scriptContent)),ref.current.appendChild(scriptElement)}else{let scriptResult=eval(scriptContent);if(typeof scriptResult=="function")return scriptResult()}},[model.key]),html`<div ref=${ref} />`}function ImportedElement({model:ee}){ReactDOM.useContext(LayoutContext);const te=ee.importSource.fallback,ne=useImportSource(ee.importSource);return ne?html`<${_ImportedElement}
      model=${ee}
      importSource=${ne}
    />`:te?typeof te=="string"?html`<div>${te}</div>`:html`<${StandardElement} model=${te} />`:html`<div />`}function _ImportedElement({model:ee,importSource:te}){ReactDOM.useContext(LayoutContext);const ne=ReactDOM.useRef(null),re=ReactDOM.useRef(null);return ReactDOM.useEffect(()=>{if(re.current=te.bind(ne.current),!te.data.unmountBeforeUpdate)return re.current.unmount},[]),ReactDOM.useEffect(()=>{if(re.current.render(ee),te.data.unmountBeforeUpdate)return re.current.unmount}),html`<div ref=${ne} />`}function useForceUpdate(){const[,ee]=ReactDOM.useState();return ReactDOM.useCallback(()=>ee({}),[])}function mountLayout(ee,te){ReactDOM.render(ReactDOM.createElement(Layout,te),ee)}function mountLayoutWithWebSocket(ee,te,ne,re){mountLayoutWithReconnectingWebSocket(ee,te,ne,re)}function mountLayoutWithReconnectingWebSocket(ee,te,ne,re,ie={everMounted:!1,reconnectAttempts:0,reconnectTimeoutRange:0}){const oe=new WebSocket(te),ae=new LazyPromise;oe.onopen=ue=>{console.info("IDOM WebSocket connected."),ie.everMounted&&ReactDOM.unmountComponentAtNode(ee),_resetOpenMountState(ie),mountLayout(ee,{loadImportSource:ne,saveUpdateHook:ae.resolve,sendEvent:le=>oe.send(JSON.stringify(le))})},oe.onmessage=ue=>{const le=JSON.parse(ue.data);ae.promise.then(fe=>fe(le))},oe.onclose=ue=>{if(!re){console.info("IDOM WebSocket connection lost.");return}const le=_nextReconnectTimeout(re,ie);console.info(`IDOM WebSocket connection lost. Reconnecting in ${le} seconds...`),setTimeout(function(){ie.reconnectAttempts++,mountLayoutWithReconnectingWebSocket(ee,te,ne,re,ie)},le*1e3)}}function _resetOpenMountState(ee){ee.everMounted=!0,ee.reconnectAttempts=0,ee.reconnectTimeoutRange=0}function _nextReconnectTimeout(ee,te){const ne=Math.floor(Math.random()*te.reconnectTimeoutRange)||1;return te.reconnectTimeoutRange=(te.reconnectTimeoutRange+5)%ee,ne}function LazyPromise(){this.promise=new Promise((ee,te)=>{this.resolve=ee,this.reject=te})}const scriptRel="modulepreload",assetsURL=function(ee){return"/_idom/"+ee},seen={},__vitePreload=function ee(te,ne,re){return!ne||ne.length===0?te():Promise.all(ne.map(ie=>{if(ie=assetsURL(ie),ie in seen)return;seen[ie]=!0;const oe=ie.endsWith(".css"),ae=oe?'[rel="stylesheet"]':"";if(document.querySelector(`link[href="${ie}"]${ae}`))return;const ue=document.createElement("link");if(ue.rel=oe?"stylesheet":scriptRel,oe||(ue.as="script",ue.crossOrigin=""),ue.href=ie,document.head.appendChild(ue),oe)return new Promise((le,fe)=>{ue.addEventListener("load",le),ue.addEventListener("error",()=>fe(new Error(`Unable to preload CSS for ${ie}`)))})})).then(()=>te())};function mountWithLayoutServer(ee,te,ne){const re=(ie,oe)=>__vitePreload(()=>oe=="NAME"?import(te.path.module(ie)):import(ie),[]).catch(ae=>{throw ae});mountLayoutWithWebSocket(ee,te.path.stream,re,ne)}function LayoutServerInfo({host:ee,port:te,path:ne,query:re,secure:ie}){const ae=`${`ws${ie?"s":""}`}://${ee}:${te}`;let ue=ne||new URL(document.baseURI).pathname;ue.endsWith("/")&&(ue=ue.slice(0,-1)),re?re=`?${re}`:re="",this.path={stream:`${ae}/_idom/stream${ue}${re}`,module:le=>`/_idom/modules/${le}`}}function mount(ee){const te=new LayoutServerInfo({host:document.location.hostname,port:document.location.port,query:queryParams.user.toString(),secure:document.location.protocol=="https:"});mountWithLayoutServer(ee,te,shouldReconnect()?45:0)}function shouldReconnect(){return queryParams.reserved.get("noReconnect")===null}const queryParams=(()=>{const ee=new URLSearchParams,te=new URLSearchParams(window.location.search);return["noReconnect"].forEach(re=>{te.get(re)!==null&&(ee.append(re,te.get(re)),te.delete(re))}),{reserved:ee,user:te}})();mount(document.getElementById("app"));
