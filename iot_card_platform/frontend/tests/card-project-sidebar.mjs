// 运行：PLAYWRIGHT_MODULE=/absolute/path/to/playwright/index.mjs node frontend/tests/card-project-sidebar.mjs
const { chromium } = await import(process.env.PLAYWRIGHT_MODULE || 'playwright');
import assert from 'node:assert/strict';
const browser = await chromium.launch({channel:'chrome',headless:true});
const page = await browser.newPage({viewport:{width:1440,height:1050}});
await page.addInitScript(() => localStorage.setItem('iot_card_access_token', JSON.stringify('local-project-ui-test')));
const state={projects:Array.from({length:12},(_,i)=>({id:i+1,name:i===0?'合肥测试项目333长名称显示检查':`项目${String(i+1).padStart(2,'0')}`,user_id:10,remark:''})), cards:[1,2,3,4].map(i=>({id:i,iccid:'8986000000000000000'+i,user_id:i===4?20:10,project_id:i===2?1:i===3?2:null,carrier:'cmcc',status:'activated',flow_size:1024,data_total:1024,data_used:128,data_used_month:64,period_type:'monthly',card_type:'single',is_pool_member:false,created_at:'2026-10-30T10:00:00',related_user_name:i===4?'下级客户':'测试账号'})),requests:[],errors:[]};
page.on('pageerror', e=>state.errors.push(e.message));
await page.route('**/api/v1/**', async route=>{
  const req=route.request(),url=new URL(req.url()),path=url.pathname.replace('/api/v1',''),q=url.searchParams;
  const body=req.postDataJSON(); state.requests.push({method:req.method(),path,query:Object.fromEntries(q),body});
  let data={};
  const scoped=()=>state.cards.filter(c=>q.get('project_id')?c.user_id===10&&c.project_id===Number(q.get('project_id')):q.get('ungrouped')==='true'?c.user_id===10&&!c.project_id:true).map(c=>({...c,project_name:state.projects.find(p=>p.id===c.project_id)?.name}));
  if(path==='/auth/profile') data={id:10,name:'项目分组测试',account:'project_test',user_level:1,status:'enable'};
  else if(path==='/menus/user/10') data=[1,2,3,4];
  else if(path==='/menus') data=[{id:1,name:'卡片管理',path:'/cards',parent_id:0,type:'directory',sort_order:1},{id:2,name:'卡片列表',path:'/cards/list',parent_id:1,type:'menu',sort_order:1},{id:3,name:'用户管理',path:'/users/list',parent_id:0,type:'menu',sort_order:2},{id:4,name:'流量池管理',path:'/pools/list',parent_id:0,type:'menu',sort_order:3}];
  else if(path==='/projects/all' && state.failProjects) { await route.fulfill({status:500,contentType:'application/json',body:JSON.stringify({code:500,msg:'测试加载失败'})}); return; }
  else if(path==='/projects/all') data=state.projects.map(p=>({...p,card_count:state.cards.filter(c=>c.user_id===10&&c.project_id===p.id).length}));
  else if(path==='/projects/order') state.projects=body.project_ids.map(id=>state.projects.find(p=>p.id===id));
  else if(path==='/projects/move-cards'){
    const success=[],skipped=[],failed=[];
    for(const id of body.iccids){const c=state.cards.find(c=>c.iccid===id&&c.user_id===10);
      if(!c) failed.push({iccid:id,error:'卡片不存在或不属于当前账号'});
      else if(body.source_project_id&&c.project_id!==body.source_project_id) failed.push({iccid:id,error:'卡片已不在当前项目'});
      else if(c.project_id===body.project_id) skipped.push({iccid:id,message:'无需变更'});
      else {c.project_id=body.project_id;success.push({iccid:id});}}
    data={success_count:success.length,skipped_count:skipped.length,failed_count:failed.length,success_list:success,skipped_list:skipped,failed_list:failed,duplicate_count:0};
  }
  else if(path==='/cards/stats') data={total:scoped().length,activated:scoped().length,suspended:0,silent:0};
  else if(path==='/cards/batch-query') {const found=scoped().filter(c=>body.includes(c.iccid));data={found,not_found:body.filter(id=>!found.some(c=>c.iccid===id))};}
  else if(path==='/cards') {const rows=scoped();data={items:rows,total:rows.length};}
  else if(path==='/cards/export') {await route.fulfill({status:200,contentType:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',body:'test export'});return;}
  else if(path==='/cards/export-history') data=[];
  else if(path==='/projects'&&req.method()==='POST'){data={id:Math.max(...state.projects.map(p=>p.id),0)+1,user_id:10,...body};state.projects.push(data);}
  else if(/^\/projects\/\d+$/.test(path)){const id=Number(path.split('/').pop());if(req.method()==='DELETE'){state.projects=state.projects.filter(p=>p.id!==id);state.cards.forEach(c=>{if(c.project_id===id)c.project_id=null;});}else {const p=state.projects.find(p=>p.id===id);Object.assign(p,body);data=p;}}
  else data={list:[],total:0};
  if ((path==='/cards' && q.get('project_id')===String(state.delayProject)) || (path==='/cards/batch-query' && state.delayBatch)) await new Promise(resolve=>setTimeout(resolve,500));
  if(path==='/projects/all' && state.delayNextProjects) { state.delayNextProjects=false; await new Promise(resolve=>setTimeout(resolve,700)); }
  await route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({code:200,data})});
});
const rows=()=>page.locator('.table-card .el-table__body-wrapper tbody tr');
const waitRows=async n=>{await page.waitForFunction(n=>document.querySelectorAll('.table-card .el-table__body-wrapper tbody tr').length===n,n);};

const nav=()=>page.getByRole('region',{name:'卡片项目导航'});
const cardList=()=>page.getByRole('menuitem',{name:'卡片列表',exact:true});
const projectList=()=>page.locator('.el-sub-menu__title:visible').filter({hasText:/^项目列表$/});
const project=id=>nav().locator(`[data-project-id="${id}"]`);
const title=()=>page.locator('.project-scope-heading h2');
const next=()=>nav().getByRole('button',{name:'下一页项目'});
const prev=()=>nav().getByRole('button',{name:'上一页项目'});
const search=()=>nav().getByRole('textbox',{name:'搜索全部项目'});
const waitFor=async fn=>{for(let i=0;i<100;i++){if(await fn())return;await page.waitForTimeout(50)}throw new Error('Condition timed out')};
const base=process.env.TEST_BASE_URL || 'http://127.0.0.1:4310';
const snapshot=process.env.TEST_SCREENSHOT || '/tmp/iot-sidebar-projects.png';
try {
 await page.goto(base+'/cards/list');
 await cardList().waitFor(); await waitRows(4);
 assert.equal(await nav().isVisible(),false);
 assert.equal(await cardList().locator('.el-sub-menu__icon-arrow').count(),0);
 await projectList().click();
 await project(1).waitFor(); await waitRows(4);
 await page.waitForTimeout(250);await page.screenshot({path:snapshot});
 assert.equal(await nav().locator('.project-row').count(),5);
 assert.equal(await title().textContent(),'全部卡片');
 const users=page.getByRole('menuitem',{name:'用户管理',exact:true});
 const initialY=(await users.boundingBox()).y;
 const pageHeight=(await nav().locator('.project-page').boundingBox()).height;
 await project(1).click(); await waitRows(1);
 await next().click(); assert.equal(await project(6).count(),1);
 assert.equal(await title().textContent(),'合肥测试项目333长名称显示检查');
 await next().click(); assert.equal(await nav().locator('.project-row').count(),2);
 assert.equal((await nav().locator('.project-page').boundingBox()).height,pageHeight);
 assert.equal((await users.boundingBox()).y,initialY);
 assert.equal(await next().isDisabled(),true);
 // 搜索全部项目、切换清空选择、URL恢复和后退。
 console.log('搜索全部项目、切换清空选择、URL恢复和后退。');
 await search().fill('项目08'); await project(8).waitFor();
 assert.match(await nav().locator('.project-pagination').textContent(),/1 \/ 1/);
 await project(8).click(); await waitRows(0);
 assert.match(page.url(),/project=8/);
 await waitFor(async()=>await search().inputValue()==='');
 await waitFor(async()=>(await nav().locator('.project-pagination').textContent()).includes('2 / 3'));
 await page.reload();await project(8).waitFor();await waitRows(0);
 assert.equal(await title().textContent(),'项目08');
 await nav().getByRole('button',{name:'未分组',exact:true}).click();await waitRows(1);
 await page.goBack();await project(8).waitFor();assert.equal(await title().textContent(),'项目08');
 // 矮窗口每页3个，下方菜单仍可见。
 console.log('矮窗口每页3个，下方菜单仍可见。');
 await page.setViewportSize({width:1440,height:760});
 await waitFor(async()=>await nav().locator('.project-row').count()===3);
 assert.equal((await nav().locator('.project-page').boundingBox()).height,102);
 assert.ok((await page.getByRole('menuitem',{name:'流量池管理',exact:true}).boundingBox()).y<720);
 await page.waitForTimeout(350);await page.screenshot({path:snapshot.replace('.png','-compact.png')});
 await page.setViewportSize({width:1440,height:1050});
 await waitFor(async()=>await nav().locator('.project-row').count()===5);
 // 同页排序、跨页位置调整，搜索时禁用拖动排序。
 console.log('同页排序、跨页位置调整，搜索时禁用拖动排序。');
 await search().fill('项目02');await project(2).waitFor();
 assert.equal(await nav().locator('.drag-handle').isDisabled(),true);
 await search().fill('');await project(1).waitFor();
 await nav().getByRole('button',{name:'拖动排序：合肥测试项目333长名称显示检查'}).dragTo(project(2));
 await waitFor(()=>state.projects[0].id===2);
 await project(2).hover();await nav().getByRole('button',{name:'项目02项目操作'}).click();
 await page.getByRole('menuitem',{name:'移至第几位',exact:true}).click();
 const prompt=page.getByRole('dialog',{name:'调整「项目02」的位置'});
 await prompt.getByRole('textbox').fill('12');await prompt.getByRole('button',{name:/确认|确定|OK/}).click();
 await waitFor(()=>state.projects.at(-1).id===2);
 assert.equal(state.projects.length,12);
 // 卡片拖动悬停翻页，右侧不切换；跨页转移后数量刷新。
 console.log('卡片拖动悬停翻页，右侧不切换；跨页转移后数量刷新。');
 await cardList().click();await waitRows(4);
 assert.equal(new URL(page.url()).searchParams.has('project'),false);
 assert.equal(await title().textContent(),'全部卡片');
 await nav().waitFor({state:'hidden'});
 await projectList().click();
 await search().fill('');
 while(!(await prev().isDisabled()))await prev().click();
 const dt=await page.evaluateHandle(()=>new DataTransfer());
 await page.locator('.card-drag-handle').first().dispatchEvent('dragstart',{dataTransfer:dt});
 await next().dispatchEvent('dragover',{dataTransfer:dt});await page.waitForTimeout(800);
 assert.match(await nav().locator('.project-pagination').textContent(),/2 \/ 3/);
 assert.equal(await title().textContent(),'全部卡片');
 const targetId=Number(await nav().locator('.project-name').first().getAttribute('data-project-id'));
 await project(targetId).dispatchEvent('dragover',{dataTransfer:dt});
 await project(targetId).dispatchEvent('drop',{dataTransfer:dt});
 const move=page.getByRole('dialog',{name:'项目转移',exact:true});await move.waitFor();
 await move.getByRole('button',{name:'确认转移'}).click();
 await move.getByText('成功 1 张，无需变更 0 张，失败 0 张').waitFor();
 assert.equal(state.cards[0].project_id,targetId);
 await move.getByRole('button',{name:'关闭',exact:true}).click();
 // 行菜单移出、项目工具栏批量弹窗支持跨页目标。
 console.log('行菜单移出、项目工具栏批量弹窗支持跨页目标。');
 await rows().first().getByRole('button',{name:'操作',exact:true}).click();
 await page.getByRole('menuitem',{name:'移出项目',exact:true}).click();
 await move.getByRole('button',{name:'确认转移'}).click();
 await move.getByText('成功 1 张，无需变更 0 张，失败 0 张').waitFor();
 assert.equal(state.cards[0].project_id,null);
 await move.getByRole('button',{name:'关闭',exact:true}).click();
 await page.getByRole('button',{name:'项目转移',exact:true}).click();
 await move.getByRole('textbox').fill('89860000000000000001');
 await move.getByRole('combobox').click();await page.getByRole('option',{name:'项目12',exact:true}).click();
 await move.getByRole('button',{name:'确认转移'}).click();
 await move.getByText('成功 1 张，无需变更 0 张，失败 0 张').waitFor();
 assert.equal(state.cards[0].project_id,12);await move.getByRole('button',{name:'关闭',exact:true}).click();
 // 新建、重命名、删除当前项目，恢复全部卡片。
 console.log('新建、重命名、删除当前项目，恢复全部卡片。');
 await nav().getByRole('button',{name:'新建项目'}).click();
 const form=page.getByRole('dialog',{name:'新增项目'});
 await form.getByPlaceholder('请输入项目名称').fill('验收项目');await form.getByRole('button',{name:'确定',exact:true}).click();
 await search().fill('验收项目');await project(13).waitFor();await project(13).click();
 await project(13).hover();await nav().getByRole('button',{name:'验收项目项目操作'}).click();
 await page.getByRole('menuitem',{name:'编辑项目',exact:true}).click();
 const edit=page.getByRole('dialog',{name:'编辑项目'});
 await edit.getByPlaceholder('请输入项目名称').fill('验收项目更名');await edit.getByRole('button',{name:'确定',exact:true}).click();
 await waitFor(async()=>await title().textContent()==='验收项目更名');
 await project(13).hover();await nav().getByRole('button',{name:'验收项目更名项目操作'}).click();
 await page.getByRole('menuitem',{name:'删除项目',exact:true}).click();
 await page.getByRole('dialog',{name:'删除项目'}).getByRole('button',{name:/确认|确定|OK/}).click();
 await waitFor(async()=>await title().textContent()==='全部卡片');await waitRows(4);
 // 列表请求乱序不能覆盖当前项目。
 console.log('列表请求乱序不能覆盖当前项目。');
 await search().fill('');while(!(await prev().isDisabled()))await prev().click();state.delayProject=1;await project(1).click();
 await search().fill('项目02');await project(2).click();await page.waitForTimeout(700);
 assert.match(await rows().textContent(),/89860000000000000003/);state.delayProject=undefined;
 // 当前项目直接URL重载、搜索无结果不改变范围，空项目固定占位。
 console.log('当前项目直接URL重载、搜索无结果不改变范围，空项目固定占位。');
 await search().fill('不存在的项目');await nav().getByText('没有匹配的项目').waitFor();
 assert.equal(await title().textContent(),'项目02');
 await search().fill('');await cardList().click();await waitRows(4);

 console.log('折叠侧栏、异常重试、空项目和账号隔离');
 await page.locator('.collapse-icon').click();
 await page.locator('.sidebar > .logo-container').waitFor();
 await page.locator('.sidebar-menu > .el-sub-menu').hover();
 await projectList().hover();
 await nav().getByRole('button',{name:'未分组',exact:true}).waitFor();
 await page.locator('.collapse-icon').click();
 await projectList().click();
 await project(1).waitFor();
 const refreshProjects=()=>page.evaluate(async()=>{const {useCardProjectsStore}=await import('/src/stores/modules/cardProjects.ts');await useCardProjectsStore().refresh()});
 state.failProjects=true;await refreshProjects();await nav().getByText('项目加载失败',{exact:false}).waitFor();
 state.failProjects=false;await nav().getByRole('button',{name:'重试',exact:true}).click();await project(1).waitFor();
 state.projects=[];await refreshProjects();await nav().getByText('暂无项目，点击 + 新建').waitFor();
 assert.equal((await nav().locator('.project-page').boundingBox()).height,170);
 assert.equal(await next().isDisabled(),true);assert.equal(await prev().isDisabled(),true);
 state.projects=[{id:1,name:'旧账号项目',user_id:10,card_count:0}];state.delayNextProjects=true;const pendingRefresh=refreshProjects();await waitFor(()=>state.delayNextProjects===false);
 state.projects=[{id:21,name:'新账号项目',user_id:21,card_count:0}];
 await page.evaluate(async()=>{const {useAuthStore}=await import('/src/stores/modules/auth.ts');const store=useAuthStore();store.userInfo={...store.userInfo,id:21};});
 await project(21).waitFor();await pendingRefresh;assert.equal(await nav().locator('.project-row').count(),1);
 assert.equal(await title().textContent(),'全部卡片');
 assert.deepEqual(state.errors,[]);
 console.log('PASS: 项目固定高度分页/末页留白/全局搜索/范围与翻页分离/URL刷新后退/矮窗口/同页排序/跨页位置调整/卡片悬停翻页转移/行菜单及粘贴跨页转移/项目增删改/异步请求乱序；无浏览器异常');
} catch(error) { await page.screenshot({path:'/tmp/iot-sidebar-failure.png',fullPage:true});throw error }
finally { await browser.close(); }
