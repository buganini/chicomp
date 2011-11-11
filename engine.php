<?php
if($_REQUEST['action']=='DECOMP'){
	$p=bsdconv_create("utf-8:zh_decomp:split:bsdconv_keyword,bsdconv");
	$s=bsdconv($p, $_POST['data']);
	bsdconv_destroy($p);
	$s=trim($s,',');
	$r=array();
	$a=explode(',',$s);
	foreach($a as $c){
		if(substr($c,0,2)=='04')
			$r[]=$c;
	}
	echo json_encode($r);
}elseif($_REQUEST['action']=='COMP'){
	$p=bsdconv_create("bsdconv:zh_comp:utf-8");
	$s=bsdconv($p, $_POST['data']);
	bsdconv_destroy($p);
	echo json_encode($s);
}elseif($_REQUEST['action']=='INFO'){
	$p=bsdconv_create("utf-8:ascii-html-info");
	$s=bsdconv($p, $_POST['data']);
	bsdconv_destroy($p);
	echo $s;
}
?>
