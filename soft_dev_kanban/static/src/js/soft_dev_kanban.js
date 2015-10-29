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
                    });
                    if (self.view.dataset.model === 'project.task'){
                        self.view.dataset.call('check_wip_limit', [self.view.datarecord.id, change['stage_id']]).done(function (r) {
                            if (r[0] != false){
                                self.do_warn('Warning', r);
                            }
                        });
                    }
                });
            }
        }
    });

};
