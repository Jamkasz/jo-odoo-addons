/**
 * Created by joelortiz on 29/10/15.
 */

openerp.soft_dev_kanban = function (instance) {

    instance.web.form.FieldStatus.include({
        on_click_stage: function (ev) {
            var self = this;
            var $li = $(ev.currentTarget);
            var val;
            if (this.field.type == "many2one") {
                val = parseInt($li.data("id"), 10);
            }
            else {
                val = $li.data("id");
            }
            if (val != self.get('value')) {
                this.view.recursive_save().done(function () {
                    var change = {};
                    change[self.name] = val;
                    self.view.dataset.write(self.view.datarecord.id, change).done(function () {
                        self.view.reload();
                        if (self.view.dataset.model === 'project.task'){
                            self.view.dataset.call('check_wip_limit', [self.view.datarecord.id, change['stage_id']]).done(function (r) {
                                if (r[0] != false){
                                    self.do_warn('Warning', r);
                                }
                            });
                            self.view.dataset.call('check_stage_limit', [change['stage_id']]).done(function (r) {
                                if (r != false){
                                    self.do_warn('Warning', r);
                                }
                            });
                            self.view.dataset.call('check_team_limit', [self.view.datarecord.id, change['stage_id']]).done(function (r) {
                                if (r[0] != false){
                                    self.do_warn('Warning', r);
                                }
                            });
                        }
                    });
                });
            }
        }
    });

    instance.web_kanban.KanbanView.include({
       on_record_moved : function(record, old_group, old_index, new_group, new_index) {
            var self = this;
            record.$el.find('[title]').tooltip('destroy');
            $(old_group.$el).add(new_group.$el).find('.oe_kanban_aggregates, .oe_kanban_group_length').hide();
            if (old_group === new_group) {
                new_group.records.splice(old_index, 1);
                new_group.records.splice(new_index, 0, record);
                new_group.do_save_sequences();
            } else {
                old_group.records.splice(old_index, 1);
                new_group.records.splice(new_index, 0, record);
                record.group = new_group;
                var data = {};
                data[this.group_by] = new_group.value;
                this.dataset.write(record.id, data, {}).done(function() {
                    record.do_reload();
                    new_group.do_save_sequences();
                    if (new_group.state.folded) {
                        new_group.do_action_toggle_fold();
                        record.prependTo(new_group.$records.find('.oe_kanban_column_cards'));
                    }
                    if (old_group != new_group){
                        if (self.dataset.model === 'project.task'){
                            self.dataset.call('check_wip_limit', [record.id, new_group.value]).done(function (r){
                               if (r[0] != false){
                                   self.do_warn('Warning', r);
                               }
                            });
                            self.dataset.call('check_stage_limit', [new_group.value]).done(function (r){
                               if (r != false){
                                   self.do_warn('Warning', r);
                               }
                            });
                            self.dataset.call('check_team_limit', [record.id, new_group.value]).done(function (r){
                               if (r[0] != false){
                                   self.do_warn('Warning', r);
                               }
                            });
                        }
                    }
                }).fail(function(error, evt) {
                    evt.preventDefault();
                    alert(_t("An error has occured while moving the record to this group: ") + error.data.message);
                    self.do_reload(); // TODO: use draggable + sortable in order to cancel the dragging when the rcp fails
                });
            }
       }
    });

};
