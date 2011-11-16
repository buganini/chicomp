<?php
if($_REQUEST['action']=='DECOMP'){
	$c=new Bsdconv("utf-8:zh_decomp:split:bsdconv_keyword,bsdconv");
	$s=$c->conv($_POST['data']);
	unset($c);
	$s=trim($s,',');
	$r=array();
	$a=explode(',',$s);
	foreach($a as $c){
		if(substr($c,0,2)=='04')
			$r[]=$c;
	}
	echo json_encode($r);
}elseif($_REQUEST['action']=='COMP'){
	$c=new Bsdconv("bsdconv:zh_comp:utf-8");
	$s=$c->conv($_POST['data']);
	unset($c);
	echo $s;
}elseif($_REQUEST['action']=='INFO'){
	$c=new Bsdconv("utf-8:ascii-html-info");
	$s=$c->conv($_POST['data']);
	unset($c);
	echo $s;
}
?>
