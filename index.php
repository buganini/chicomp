<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
<script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jquery/1.5.0/jquery.min.js"></script>
<script type="text/javascript" src="http://ajax.googleapis.com/ajax/libs/jqueryui/1.8.9/jquery-ui.min.js"></script>
<style type="text/css">
.hovered {
	border-left: solid 2px #abf;
}
.redback {
	background-color: #fdd;
}
img {
	margin: 1px;
}
</style>
</head>
<body>
<input type="text" id="text" /><input type="button" id="decomp" value="Decomp" />
<hr />
<span id="edit"></span><input type="button" id="comp" value="Comp" /><input type="button" id="clear" value="Clear" />
<hr />
<div id="info"></div>
<textarea id="result"></textarea>
<hr />
<h3>Hints:</h3>
1. Drag component to rearrange<br />
2. Double click to duplicate component<br/>
3. Drag into [&#x4EA9;] to delete component
<hr />
<span id="comps">
<?php
	function ucmp($a,$b){
		$a=base_convert(substr($a,2),16,10);
		$b=base_convert(substr($b,2),16,10);
		return $a-$b;
	}
	$files=scandir('images');
	usort($files,'ucmp');
	foreach($files as $file){
		if($file=='.' || $file=='..') continue;
		$n=str_replace('.gif','',$file);
		echo '<img src="images/'.$file.'" title="'.$n.'" alt="'.$n.'" />';
	}
?></span>
<script type="text/javascript">
	sequence=[]

	function dropfunc(event, ui){
		var t=sequence
		var n=ui.draggable.attr('no')
		sequence=[]
		for(var i=0;i<t.length;++i){
			if(i==n)
				continue
			if(i==$(this).attr('no'))
				sequence[sequence.length]=t[n]
			sequence[sequence.length]=t[i]
		}
		if(i==$(this).attr('no'))
			sequence[sequence.length]=t[n]
		redraw()
	}

	function redraw(){
		$('#edit').html('')
		for(var i=0;i<sequence.length;++i){
			var o=$('<img src="images/'+sequence[i]+'.gif" title="'+sequence[i]+'" no="'+i+'" />')
			$('#edit').append(o)
			o.dblclick(function(){
				sequence[sequence.length]=sequence[$(this).attr('no')]
				redraw()
			})
			o.draggable({
				containment: '#edit'
			})
			o.droppable({
				hoverClass: 'hovered',
				drop: dropfunc
			})
		}
		var o=$('<img src="images/null.gif" no="'+i+'" />')
		$('#edit').append(o)
		o.dblclick(function(){
			sequence[sequence.length]=sequence[$(this).attr('no')]
			redraw()
		})
		o.droppable({
			hoverClass: 'hovered',
			drop: dropfunc
		})
		var o=$('<a style="margin:3em; padding: 0.5em;">[&#x4EA9;]</a>')
		$('#edit').append(o)
		o.droppable({
			hoverClass: 'redback',
			drop: function(event, ui){
				var t=sequence
				sequence=[]
				for(var i=0;i<t.length;++i){
					if(i!=ui.draggable.attr('no'))
						sequence[sequence.length]=t[i]
				}
				redraw()
			}
		})
	}
	$('#decomp').click(function(){
		$.ajax({
			url: "engine.php",
			type: "POST",
			data: {
				action: 'DECOMP',
				data : $('#text').val()
			},
			dataType: "json",
			async:false,
			success: function(j){
				for(var i=0;i<j.length;++i){
					sequence[sequence.length]=j[i]
				}
				redraw()
			}
		});
	})
	$('#comp').click(function(){
		$.ajax({
			url: "engine.php",
			type: "POST",
			data: {
				action: 'COMP',
				data : sequence.join(',')
			},
			dataType: "text",
			async:false,
			success: function(j){
				$('#result').val(j)
						$.ajax({
							url: "engine.php",
							type: "POST",
							data: {
								action: 'INFO',
								data : j
							},
							dataType: "html",
							async:false,
							success: function(j){
								$('#info').html(j)
							}
						});
			}
		});
	})
	$('#clear').click(function(){
		sequence=[]
		redraw()
	})
	$('#comps img').click(function(){
		sequence[sequence.length]=$(this).attr('alt')
		redraw()
	})
	redraw()
	if(document.location.hash){
		$("#text").val(document.location.hash.substring(1));
		$.ajax({
			url: "engine.php",
			type: "POST",
			data: {
				action: 'DECOMP',
				data : $('#text').val()
			},
			dataType: "json",
			async:false,
			success: function(j){
				for(var i=0;i<j.length;++i){
					sequence[sequence.length]=j[i]
				}
				redraw()
				$("#comp").click();
			}
		})
	}
</script>
</body>
</html>
