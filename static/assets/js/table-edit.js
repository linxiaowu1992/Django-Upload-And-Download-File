
// Data Tables - Config
(function($) {

	'use strict';

	// we overwrite initialize of all datatables here
	// because we want to use select2, give search input a bootstrap look
	// keep in mind if you overwrite this fnInitComplete somewhere,
	// you should run the code inside this function to keep functionality.
	//
	// there's no better way to do this at this time :(
	if ( $.isFunction( $.fn[ 'dataTable' ] ) ) {

		$.extend(true, $.fn.dataTable.defaults, {
			sDom: "<'row datatables-header form-inline'<'col-sm-12 col-md-6'l><'col-sm-12 col-md-6'f>r><'table-responsive't><'row datatables-footer'<'col-sm-12 col-md-6'i><'col-sm-12 col-md-6'p>>",
			oLanguage: {
				sLengthMenu: '_MENU_ records per page',
				sProcessing: '<i class="fa fa-spinner fa-spin"></i> Loading'
			},
			fnInitComplete: function( settings, json ) {
				// select 2
				if ( $.isFunction( $.fn[ 'select2' ] ) ) {
					$('.dataTables_length select', settings.nTableWrapper).select2({
						minimumResultsForSearch: -1
					});
				}

				var options = $( 'table', settings.nTableWrapper ).data( 'plugin-options' ) || {};

				// search
				var $search = $('.dataTables_filter input', settings.nTableWrapper);

				$search
					.attr({
						placeholder: typeof options.searchPlaceholder !== 'undefined' ? options.searchPlaceholder : 'Search'
					})
					.addClass('form-control');

				if ( $.isFunction( $.fn.placeholder ) ) {
					$search.placeholder();
				}
			}
		});

	}

}).apply( this, [ jQuery ]);


/*Datatable - editable*/
(function( $ ) {

	'use strict';

	var EditableTable = {

		options: {
			addButton: '#addToTable',
			table: '#periodTable',
			dialog: {
				wrapper: '#dialog',
				cancelButton: '#dialogCancel',
				confirmButton: '#dialogConfirm',
			}
		},

		initialize: function() {
			this
				.setVars()
				.build()
				.events();
		},

		setVars: function() {
			this.$table				= $( this.options.table );
			this.$addButton			= $( this.options.addButton );

			// dialog
			this.dialog				= {};
			this.dialog.$wrapper	= $( this.options.dialog.wrapper );
			this.dialog.$cancel		= $( this.options.dialog.cancelButton );
			this.dialog.$confirm	= $( this.options.dialog.confirmButton );

			return this;
		},

		build: function() {
			this.datatable = this.$table.DataTable({
			"ajax": {
				"url": "/jgsystem/data_get",
				"data": function (d) {
					d.type = 'getPeriodData'
				},
			},
			"processing": true,
			"serverSide": true,
			"bAutoWidth":false,
			"columns": [
				{
					"data": null,
					"orderable": false,
				},
				{'data':'name'},
				{'data':'task'},
				{'data':'args'},
				{'data':'kwargs'},
				{'data':null},
				{'data':'last_run_at'},
				{'data':'description'},
				{'data':'crontab'},
				{'data':null}
			],
			"columnDefs": [
				// 用来生成checkbox
				{
					'targets': 0,
					'searchable':false,
					'orderable':false,
					'className': 'dt-body-center',
					'render': function (data, type, full, meta){
					 return '<input type="checkbox" value="'+full.id+'">';
					},
				},	
				{
					'targets': 5,
					'searchable':false,
					'orderable':false,
					'className': 'dt-body-center',
					'render': function (a, b, c, d){
						if (c.enabled == 1) {
					 		return '<span class="label label-success label-sm">ON</span>';
					 	}else{
					 		return '<span class="label label-danger label-sm">OFF</span>';
					 	}
					},
				},								
				{
                targets: 9,
                render: function(a, b, c, d) {
                	var html
                    html = '<div class="actions">'+
                    			'<a href="#" class="hidden on-editing save-row"><i class="fa fa-save"></i></a>'+
								'<a href="#" class="hidden on-editing cancel-row"><i class="fa fa-times"></i></a>'+
								'<a href="#" class="on-default edit-row"><i class="fa fa-pencil"></i></a>'+
								'<a href="#" class="on-default remove-row"><i class="fa fa-trash-o"></i></a>'+
								'</div>'
                    return html
                }
            	},
			],			
		
			'language': {
				"sProcessing": "处理中...",
				"sLengthMenu": "显示 _MENU_ 项结果",
				"sZeroRecords": "没有匹配结果",
				"sInfo": "显示第 _START_ 至 _END_ 项结果，共 _TOTAL_ 项",
				"sInfoEmpty": "显示第 0 至 0 项结果，共 0 项",
				"sInfoFiltered": "(由 _MAX_ 项结果过滤)",
				"sInfoPostFix": "",
				"sSearch": "搜索:",
				"sUrl": "",
				"sEmptyTable": "表中数据为空",
				"sLoadingRecords": "载入中...",
				"sInfoThousands": ",",
				"oPaginate": {
					"sFirst": "首页",
					"sPrevious": "上页",
					"sNext": "下页",
					"sLast": "末页"
				},
				"oAria": {
					"sSortAscending": ": 以升序排列此列",
					"sSortDescending": ": 以降序排列此列"
				}
			},
		
		
		})	

			window.dt = this.datatable;

			return this;
		},

		events: function() {
			var _self = this;

			this.$table
				.on('click', 'a.save-row', function( e ) {
					e.preventDefault();

					_self.rowSave( $(this).closest( 'tr' ) );
				})
				.on('click', 'a.cancel-row', function( e ) {
					e.preventDefault();

					_self.rowCancel( $(this).closest( 'tr' ) );
				})
				.on('click', 'a.edit-row', function( e ) {
					e.preventDefault();

					_self.rowEdit($(this).closest('tr'));
				})
				.on( 'click', 'a.remove-row', function( e ) {
					e.preventDefault();

					var $row = $(this).closest( 'tr' );

					$.magnificPopup.open({
						items: {
							src: '#dialog',
							type: 'inline'
						},
						preloader: false,
						modal: true,
						callbacks: {
							change: function() {
								_self.dialog.$confirm.on( 'click', function( e ) {
									e.preventDefault();

									_self.rowRemove( $row );
									$.magnificPopup.close();
								});
							},
							close: function() {
								_self.dialog.$confirm.off( 'click' );
							}
						}
					});
				});

			this.$addButton.on( 'click', function(e) {
				e.preventDefault();

				_self.rowAdd();
			});

			this.dialog.$cancel.on( 'click', function( e ) {
				e.preventDefault();
				$.magnificPopup.close();
			});

			return this;
		},

		// ==========================================================================================
		// ROW FUNCTIONS
		// ==========================================================================================
		rowAdd: function() {
			this.$addButton.attr({ 'disabled': 'disabled' });

			var actions,
				data,
				$row;

			actions = [
				'<a href="#" class="hidden on-editing save-row"><i class="fa fa-save"></i></a>',
				'<a href="#" class="hidden on-editing cancel-row"><i class="fa fa-times"></i></a>',
				'<a href="#" class="on-default edit-row"><i class="fa fa-pencil"></i></a>',
				'<a href="#" class="on-default remove-row"><i class="fa fa-trash-o"></i></a>'
			].join(' ');

			data = this.datatable.row.add([ '', '', '', actions ]);
			$row = this.datatable.row( data[0] ).nodes().to$();

			$row
				.addClass( 'adding' )
				.find( 'td:last' )
				.addClass( 'actions' );

			this.rowEdit( $row );

			this.datatable.order([0,'asc']).draw(); // always show fields
		},

		rowCancel: function( $row ) {
			var _self = this,
				$actions,
				i,
				data;

			if ( $row.hasClass('adding') ) {
				this.rowRemove( $row );
			} else {

				data = this.datatable.row( $row.get(0) ).data();
				this.datatable.row( $row.get(0) ).data( data );

				$actions = $row.find('td.actions');
				if ( $actions.get(0) ) {
					this.rowSetActionsDefault( $row );
				}

				this.datatable.draw();
			}
		},
		sortRowData: function(data){
			var tempList=new Array()
			tempList.push(data['name'])
			tempList.push(data['task'])
			tempList.push(data['args'])
			tempList.push(data['kwargs'])
			tempList.push(data['enabled'])
			tempList.push(data['last_run_at'])
			tempList.push(data['description'])
			tempList.push(data['crontab'])
			return tempList
		},
		rowEdit: function( $row ) {
			var _self = this,
				data;
			var dataList=new Array()
			data = this.datatable.row( $row.get(0) ).data();
			dataList = _self.sortRowData(data)
			$row.children( 'td' ).slice(1).each(function( i ) {
				var $this = $( this );
				if ( $this.children('div').hasClass('actions') ) {
					_self.rowSetActionsEditing( $row );
				} else {
					$this.html( '<input type="text" class="form-control input-block" value="' + dataList[i] + '"/>' );
				}
			});
		},
		formatSaveData: function(data){
			var dataDict = {}
			dataDict['id'] = data[0]
			dataDict['name'] = data[1]
			dataDict['task'] = data[2]
			dataDict['args'] = data[3]
			dataDict['kwargs'] = data[4]
			dataDict['enabled'] = data[5]
			dataDict['last_run_at'] = data[6]
			dataDict['description'] = data[7]
			dataDict['crontab'] = data[8]
			return dataDict
		},
		rowSave: function( $row ) {
			var _self     = this,
				$actions,
				values    = [];

			if ( $row.hasClass( 'adding' ) ) {
				this.$addButton.removeAttr( 'disabled' );
				$row.removeClass( 'adding' );
			}

			values = $row.find('td').map(function() {
				var $this = $(this);

				if ( $this.children('div').hasClass('actions') ) {
					_self.rowSetActionsDefault( $row );
					return _self.datatable.cell( this ).data();
				} else {
					return $.trim( $this.find('input').val() );
				}
			});
			console.log(values)
			console.log(_self.formatSaveData(values))
			console.log(this.datatable.row( $row.get(0) ).data())
			this.datatable.row( $row.get(0) ).data( _self.formatSaveData(values) );

			$actions = $row.find('td div.actions');
			if ( $actions.get(0) ) {
				this.rowSetActionsDefault( $row );
			}

			this.datatable.draw();
		},

		rowRemove: function( $row ) {
			if ( $row.hasClass('adding') ) {
				this.$addButton.removeAttr( 'disabled' );
			}

			this.datatable.row( $row.get(0) ).remove().draw();
		},

		rowSetActionsEditing: function( $row ) {
			$row.find( '.on-editing' ).removeClass( 'hidden' );
			$row.find( '.on-default' ).addClass( 'hidden' );
		},

		rowSetActionsDefault: function( $row ) {
			$row.find( '.on-editing' ).addClass( 'hidden' );
			$row.find( '.on-default' ).removeClass( 'hidden' );
		}

	};

	$(function() {
		EditableTable.initialize();
	});

}).apply( this, [ jQuery ]);